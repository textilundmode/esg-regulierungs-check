"""Volltext-basierte Regulierungsanalyse mit Provider-Switch.

Unterstützt Ollama (lokal/kostenfrei), Anthropic Claude und OpenAI.
Für jede Regulierung:
  1. Volltext aus DB-Cache holen (fetcher.py kümmert sich ums Laden/Aktualisieren)
  2. Profil + Kriterien + Volltext-Auszug an LLM
  3. LLM gibt JSON mit applies/reason/passage zurück
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import queue
import re
import threading
import time
from typing import Callable

# Eine einzige englische Basis-System-Prompt + sprachspezifische Anweisung
# am Ende. So skaliert es sauber auf beliebig viele Sprachen.
_SYSTEM_BASE = """You are a precise ESG compliance analyst.
You receive a company profile, the applicability criteria of a regulation
and the (truncated) full text of the law.

CRITICAL FORMATTING:
- Your ENTIRE response MUST be a single valid JSON object.
- NO preamble, NO explanation, NO markdown, NO reasoning before or after the JSON.
- Start your response DIRECTLY with {{ and end with }}.

Schema:
{{
  "applies": "ja" | "nein" | "moeglich",
  "reason": "2-4 short sentences ({lang_name}), max. 80 words",
  "passage": "Short verbatim quote from the full text (preferred) or a paraphrase with article/paragraph reference (max. 50 words, same language as reason)"
}}

Content rules:
- "ja" (yes) only if all thresholds/criteria are clearly met.
- "moeglich" (possible) if information is missing, special rules may apply, or thresholds are close.
- "nein" (no) if clearly outside the scope.
- "reason" is MANDATORY for all three cases and must concretely explain WHY the regulation applies / may apply / does not apply (referencing profile values such as headcount, revenue, sector, sites). Never leave empty.
- Write "reason" and "passage" in {lang_name}. Keep the "applies" values exactly as ja/nein/moeglich.
- Keep reason and passage concise so the JSON remains complete."""

_LANG_NAMES = {
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "it": "Italian",
    "zh": "Simplified Chinese (Mandarin)",
}


def _system_prompt(language: str) -> str:
    name = _LANG_NAMES.get(language, "German")
    return _SYSTEM_BASE.format(lang_name=name)


PROFILE_TEMPLATE = """COMPANY PROFILE:
Name: {name}
Legal form: {legal_form}
Group structure: {group_role}
Total employees: {employees}
Employees in Germany: {employees_de}
Net revenue (EUR/year): {revenue_eur}
Balance sheet total (EUR): {balance_sheet_eur}
Industry: {branch}
B2C business: {b2c}
Capital-market oriented: {listed}
Environmental claims/labels in marketing: {env_claims}
Product categories: {product_categories}
Sites:
{sites_block}"""

_USER_TEMPLATE = """{profile}

REGULATION: {reg_name} ({reg_full})
Source: {reg_url}
Relevant article/section: {article}

Applicability criteria (summary):
{criteria}

FULL-TEXT EXTRACT (truncated):
---
{fulltext}
---

Evaluate strictly and respond as JSON per the schema."""


def _format_profile(profile: dict) -> str:
    sites = profile.get("sites", []) or []
    if sites:
        sites_block = "\n".join(
            f"- {s.get('count', 0)}x {s.get('type', '-')} in {s.get('location', '-')}"
            for s in sites
        )
    else:
        sites_block = "- none -"
    products = profile.get("product_categories") or []
    product_block = ", ".join(products) if products else "none"
    return PROFILE_TEMPLATE.format(
        name=profile.get("name") or "(unnamed)",
        legal_form=profile.get("legal_form") or "-",
        group_role=profile.get("group_role") or "-",
        employees=profile.get("employees") or 0,
        employees_de=profile.get("employees_de") or 0,
        revenue_eur=f"{(profile.get('revenue_eur') or 0):,.0f}".replace(",", "."),
        balance_sheet_eur=f"{(profile.get('balance_sheet_eur') or 0):,.0f}".replace(",", "."),
        branch=profile.get("branch") or "-",
        b2c="yes" if profile.get("b2c") else "no",
        listed="yes" if profile.get("listed") else "no",
        env_claims="yes" if profile.get("env_claims") else "no",
        product_categories=product_block,
        sites_block=sites_block,
    )


def profile_hash(profile: dict) -> str:
    keys = [
        "name", "employees", "employees_de", "revenue_eur", "balance_sheet_eur", "branch",
        "b2c", "listed", "env_claims", "legal_form", "group_role",
        "sites", "product_categories", "language",
    ]
    stable = {k: profile.get(k) for k in keys}
    stable["sites"] = sorted(
        ({"type": s.get("type"), "location": s.get("location"), "count": s.get("count")}
         for s in (stable["sites"] or [])),
        key=lambda d: (d["type"] or "", d["location"] or ""),
    )
    stable["product_categories"] = sorted(stable["product_categories"] or [])
    return hashlib.sha256(json.dumps(stable, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def reg_hash(reg: dict) -> str:
    return hashlib.sha256(reg["criteria"].encode()).hexdigest()[:16]


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text[3:]
        if text.lower().startswith("json"):
            text = text[4:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    return text


def _extract_json(text: str) -> dict:
    """Robuste JSON-Extraktion.

    Versucht der Reihe nach: direktes parse, klammer-balanciertes Substring,
    trailing-comma-cleanup. Wirft ValueError wenn alles scheitert.
    """
    text = _strip_fences(text or "").strip()
    if not text:
        raise ValueError("leere Antwort")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Finde erstes { und das passende schließende } (mit String-Awareness)
    start = text.find("{")
    if start < 0:
        raise ValueError(f"kein JSON-Objekt gefunden: {text[:120]!r}")
    depth = 0
    in_string = False
    escape = False
    end = -1
    for i in range(start, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end < 0:
        raise ValueError(f"kein vollständiges JSON-Objekt: {text[start:start+200]!r}")

    snippet = text[start:end]
    # trailing commas vor } oder ] entfernen
    snippet = re.sub(r",(\s*[}\]])", r"\1", snippet)
    return json.loads(snippet)


def _normalize_applies(val: str) -> str:
    """Normalisiert applies-Wert sprachunabhängig auf ja|nein|moeglich.

    Akzeptiert DE, EN, ES, FR, IT, ZH.
    """
    a = (val or "").lower().strip()
    a = a.replace("ö", "oe").replace("ä", "ae").replace("ü", "ue").replace("ß", "ss")
    # Alle Sprachvarianten auf DE-Basis mappen
    yes_set = {
        "yes", "true", "applies",                    # EN
        "sí", "si", "aplica", "se aplica",           # ES
        "oui", "s'applique", "applicable",           # FR
        "sì", "si applica",                          # IT
        "是", "适用",                                 # ZH
    }
    no_set = {
        "no", "false", "does not apply", "not applicable",  # EN
        "nein",                                             # DE (passthrough)
        "no aplica", "no se aplica",                        # ES
        "non", "ne s'applique pas", "pas applicable",       # FR
        "non si applica", "non applicabile",                # IT
        "否", "不适用",                                     # ZH
    }
    maybe_set = {
        "possible", "maybe", "may apply", "could apply", "possibly",  # EN
        "moeglich",                                                    # DE
        "posible", "puede aplicar", "quizás", "quizas",                # ES
        "possible (fr)", "peut s'appliquer", "peut-être", "peut-etre", # FR
        "possibile", "potrebbe applicarsi", "può applicarsi",          # IT
        "可能", "可能适用",                                             # ZH
    }
    # ZH/entity-Zeichen nicht durch lower/replace verändert → direkter Vergleich
    raw = (val or "").strip()
    if raw in ("是", "适用"):
        return "ja"
    if raw in ("否", "不适用"):
        return "nein"
    if raw in ("可能", "可能适用"):
        return "moeglich"
    if a in yes_set:
        return "ja"
    if a in no_set:
        return "nein"
    if a in maybe_set:
        return "moeglich"
    return a if a in ("ja", "nein", "moeglich") else "moeglich"


def _enrich(reg: dict, parsed: dict) -> dict:
    return {
        "nr": reg["nr"],
        "key": reg["key"],
        "name": reg["name"],
        "full_name": reg["full_name"],
        "url": reg["url"],
        "scope": reg["scope"],
        "article": reg.get("key_article", ""),
        "applies": _normalize_applies(parsed.get("applies")),
        "reason": parsed.get("reason", ""),
        "passage": parsed.get("passage", "-"),
    }


# ---------- Provider-Abstraktion ----------
class LLMClient:
    def __init__(self) -> None:
        self.provider = os.getenv("LLM_PROVIDER", "ollama").lower().strip()
        if self.provider == "ollama":
            from openai import AsyncOpenAI
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
            self.client = AsyncOpenAI(base_url=f"{host}/v1", api_key="ollama")
            self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
            self.extra = {"extra_body": {"options": {"num_ctx": int(os.getenv("OLLAMA_CTX", "16384"))}}}
        elif self.provider == "openai":
            from openai import AsyncOpenAI
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise RuntimeError("OPENAI_API_KEY fehlt.")
            base_url = os.getenv("OPENAI_BASE_URL") or None
            self.client = AsyncOpenAI(api_key=key, base_url=base_url)
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            self.extra = {}
        elif self.provider == "google":
            import httpx as _httpx
            self.model = os.getenv("GOOGLE_MODEL") or os.getenv("OPENAI_MODEL", "gemini-2.5-flash")
            self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise RuntimeError("GOOGLE_API_KEY fehlt.")
            self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        elif self.provider == "anthropic":
            from anthropic import AsyncAnthropic
            key = os.getenv("ANTHROPIC_API_KEY")
            if not key:
                raise RuntimeError("ANTHROPIC_API_KEY fehlt.")
            self.client = AsyncAnthropic(api_key=key)
            self.model = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")
            self.extra = {}
        else:
            raise RuntimeError(f"Unbekannter LLM_PROVIDER: {self.provider}")

    async def ask(self, system: str, user: str, max_tokens: int = 1500, json_mode: bool = True) -> str:
        if self.provider in ("ollama", "openai"):
            kwargs: dict = {
                "model": self.model,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "max_tokens": max_tokens,
                "temperature": 0.0,
                **self.extra,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            try:
                resp = await self.client.chat.completions.create(**kwargs)
            except Exception as e:  # noqa: BLE001
                if json_mode and ("response_format" in str(e) or "json_object" in str(e)):
                    kwargs.pop("response_format", None)
                    resp = await self.client.chat.completions.create(**kwargs)
                else:
                    raise
            return resp.choices[0].message.content or ""
        elif self.provider == "google":
            import httpx as _httpx
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            body = {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {
                    "temperature": 0.0,
                    "maxOutputTokens": max_tokens,
                    "responseMimeType": "application/json" if json_mode else "text/plain",
                },
            }
            async with _httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(url, json=body)
                resp.raise_for_status()
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:  # anthropic
            resp = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return resp.content[0].text


def _parse_retry_after(err_str: str) -> float:
    m = re.search(r"retry[-_ ]?after[\"':\s]*([0-9.]+)", err_str, re.I)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return 0.0


async def _analyze_one(client: LLMClient, profile_block: str, reg: dict, fulltext: str, language: str) -> dict:
    system = _system_prompt(language)
    fulltext_placeholder = "(full text unavailable)"
    user_msg = _USER_TEMPLATE.format(
        profile=profile_block,
        reg_name=reg["name"],
        reg_full=reg["full_name"],
        reg_url=reg["url"],
        article=reg.get("key_article", ""),
        criteria=reg["criteria"],
        fulltext=fulltext[:int(os.getenv("FULLTEXT_MAX_CHARS", "40000"))] if fulltext else fulltext_placeholder,
    )
    last_error: str | None = None
    for attempt in range(4):
        try:
            text = await client.ask(system, user_msg, max_tokens=1500)
            parsed = _extract_json(text)
            return _enrich(reg, parsed)
        except (json.JSONDecodeError, ValueError) as e:
            # Modell hat Müll statt JSON geliefert -> kurz warten + nochmal
            last_error = f"JSON-Parse: {e}"
            await asyncio.sleep(0.6)
        except Exception as e:  # noqa: BLE001
            last_error = str(e)
            if "429" in last_error or "rate_limit" in last_error.lower():
                wait = _parse_retry_after(last_error) or 60.0
                await asyncio.sleep(min(wait + 1, 75))
            else:
                await asyncio.sleep(1.5 * (attempt + 1))
    return {**_enrich(reg, {}), "applies": "error", "reason": last_error or "unbekannter Fehler", "passage": "-"}


class RateLimiter:
    """Async sliding-window rate limiter. Begrenzt auf rpm Anfragen pro 60s."""

    def __init__(self, rpm: int) -> None:
        self.rpm = max(1, rpm)
        self.timestamps: list[float] = []
        self.lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self.lock:
            now = time.time()
            self.timestamps = [t for t in self.timestamps if now - t < 60.0]
            if len(self.timestamps) >= self.rpm:
                wait = 60.0 - (now - self.timestamps[0]) + 0.2
                if wait > 0:
                    await asyncio.sleep(wait)
                    now = time.time()
                    self.timestamps = [t for t in self.timestamps if now - t < 60.0]
            self.timestamps.append(now)


async def _run(profile: dict, jobs: list[tuple[dict, str]], result_cb: Callable[[dict], None]) -> None:
    client = LLMClient()
    profile_block = _format_profile(profile)
    language = (profile.get("language") or "de").lower()
    if language not in ("de", "en", "es", "fr", "it", "zh"):
        language = "de"

    concurrency = int(os.getenv("LLM_CONCURRENCY", "4"))
    rpm = int(os.getenv("LLM_RPM", "18"))   # 18 statt 20 = Sicherheitspuffer
    sem = asyncio.Semaphore(max(1, concurrency))
    limiter = RateLimiter(rpm)

    async def bound(reg: dict, fulltext: str) -> None:
        async with sem:
            await limiter.acquire()
            res = await _analyze_one(client, profile_block, reg, fulltext, language)
            result_cb(res)

    await asyncio.gather(*(bound(reg, ft) for reg, ft in jobs))


def analyze_streaming(
    profile: dict,
    jobs: list[tuple[dict, str]],
    cached_hits: list[dict] | None = None,
) -> "queue.Queue[dict | None]":
    """Startet Analyse im Hintergrund-Thread.

    jobs  = Liste (Regulierung, Volltext) für Misses (echt zu analysieren)
    cached_hits = bereits gültige Cache-Einträge (werden sofort gepusht)
    """
    q: queue.Queue[dict | None] = queue.Queue()
    for hit in (cached_hits or []):
        q.put({**hit, "_from_cache": True})

    def worker() -> None:
        try:
            if jobs:
                asyncio.run(_run(profile, jobs, lambda r: q.put(r)))
        except Exception as e:  # noqa: BLE001
            for reg, _ in jobs:
                q.put({**_enrich(reg, {}), "applies": "error", "reason": f"Setup-Fehler: {e}", "passage": "-"})
        finally:
            q.put(None)

    threading.Thread(target=worker, daemon=True).start()
    return q
