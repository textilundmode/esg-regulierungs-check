"""Lädt Gesetzestexte aus dem Internet, extrahiert Klartext, cached sie in SQLite.

ETag/Last-Modified werden genutzt, um bei erneutem Fetch nur zu aktualisieren
wenn sich wirklich etwas geändert hat. So wird "Aktualitätscheck" billig.
"""
from __future__ import annotations

import io
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

from db import DB_PATH


USER_AGENT = "ESG-Regulierungs-Check/1.0 (+https://localhost)"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_fetcher() -> None:
    with _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS law_texts (
                reg_key TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'de',
                url TEXT NOT NULL,
                text TEXT NOT NULL,
                etag TEXT,
                last_modified TEXT,
                fetched_at TEXT NOT NULL,
                source_status INTEGER,
                PRIMARY KEY (reg_key, language)
            )
            """
        )
        # Migration: alte Tabelle ohne language → language='de' setzen (idempotent)
        cols = {row[1] for row in c.execute("PRAGMA table_info(law_texts)").fetchall()}
        if "language" not in cols:
            c.execute("ALTER TABLE law_texts ADD COLUMN language TEXT NOT NULL DEFAULT 'de'")


def _extract_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    main = soup.find("main") or soup.find(id=re.compile("content|main|text", re.I)) or soup.body or soup
    text = main.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_pdf(data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = []
        # max 60 Seiten (reicht für Anwendungsbereich + Kernartikel)
        for i, page in enumerate(reader.pages[:60]):
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                continue
        text = "\n".join(pages)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
    except Exception as e:  # noqa: BLE001
        return f"[PDF-Extraktion fehlgeschlagen: {e}]"


_EURLEX_LANG_MAP = {
    "de": ("deu", "DE"),
    "en": ("eng", "EN"),
    "es": ("spa", "ES"),
    "fr": ("fra", "FR"),
    "it": ("ita", "IT"),
    # ZH wird auf EN gemappt (EUR-Lex hat kein Chinesisch)
    "zh": ("eng", "EN"),
}

_ACCEPT_LANG_MAP = {
    "de": "de,en;q=0.7",
    "en": "en,de;q=0.7",
    "es": "es,en;q=0.7,de;q=0.5",
    "fr": "fr,en;q=0.7,de;q=0.5",
    "it": "it,en;q=0.7,de;q=0.5",
    "zh": "en,de;q=0.7",  # ZH → EN-Text
}


def _accept_language(lang: str) -> str:
    return _ACCEPT_LANG_MAP.get(lang, "de,en;q=0.7")


def _localized_url(url: str, lang: str) -> str:
    """EUR-Lex unterstützt /oj/<3-letter> bzw. /legal-content/<2-letter>/.
    Andere URLs (z.B. gesetze-im-internet.de) unverändert.
    """
    three, two = _EURLEX_LANG_MAP.get(lang, ("deu", "DE"))
    if "eur-lex.europa.eu" in url and url.rstrip("/").endswith("/oj"):
        return url.rstrip("/") + f"/{three}"
    if "eur-lex.europa.eu/legal-content/" in url:
        # Ersetze /DE/ bzw. /EN/ / etc. durch Zielsprache
        import re as _re
        return _re.sub(r"/legal-content/[A-Z]{2}/", f"/legal-content/{two}/", url, count=1)
    return url


def _fetch_url(reg: dict) -> str:
    """Welche URL soll der Fetcher laden?

    Bei EU-Regularien zeigt 'url' auf die EUR-Lex-Suche (UI-Verlinkung),
    und 'text_url' enthält den kanonischen ELI/CELEX-Link für den Volltext.
    Fehlt 'text_url', wird 'url' verwendet (z.B. DE-Gesetze).
    """
    return reg.get("text_url") or reg["url"]


def fetch_law_text(reg: dict, *, language: str = "de", force: bool = False) -> dict:
    """Lädt den Gesetzestext und liefert {text, fetched_at, is_new, error, status}.

    Nutzt ETag/Last-Modified für conditional-GET. Bei 304 wird der Cache-Text
    zurückgegeben. Bei Fehlern mit vorhandenem Cache: Cache-Text zurück + error.
    """
    init_fetcher()
    url = _localized_url(_fetch_url(reg), language)
    with _conn() as c:
        row = c.execute(
            "SELECT text, etag, last_modified, fetched_at FROM law_texts "
            "WHERE reg_key = ? AND language = ?",
            (reg["key"], language),
        ).fetchone()

    headers = {"User-Agent": USER_AGENT, "Accept-Language": _accept_language(language)}
    if row and not force:
        if row["etag"]:
            headers["If-None-Match"] = row["etag"]
        if row["last_modified"]:
            headers["If-Modified-Since"] = row["last_modified"]

    try:
        with httpx.Client(timeout=30, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
    except Exception as e:  # noqa: BLE001
        if row:
            return {"text": row["text"], "fetched_at": row["fetched_at"], "is_new": False, "error": str(e), "status": -1}
        return {"text": "", "fetched_at": None, "is_new": False, "error": str(e), "status": -1}

    if resp.status_code == 304 and row:
        return {"text": row["text"], "fetched_at": row["fetched_at"], "is_new": False, "error": None, "status": 304}

    if resp.status_code >= 400:
        if row:
            return {"text": row["text"], "fetched_at": row["fetched_at"], "is_new": False,
                    "error": f"HTTP {resp.status_code}", "status": resp.status_code}
        return {"text": "", "fetched_at": None, "is_new": False,
                "error": f"HTTP {resp.status_code}", "status": resp.status_code}

    content_type = (resp.headers.get("content-type") or "").lower()
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        text = _extract_pdf(resp.content)
    else:
        text = _extract_html(resp.text)

    max_chars = int(os.getenv("FULLTEXT_MAX_CHARS", "40000"))
    text = text[:max_chars]

    etag = resp.headers.get("etag") or ""
    last_mod = resp.headers.get("last-modified") or ""
    now = datetime.utcnow().isoformat()
    with _conn() as c:
        c.execute(
            """
            INSERT INTO law_texts (reg_key, language, url, text, etag, last_modified, fetched_at, source_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(reg_key, language) DO UPDATE SET
                url=excluded.url,
                text=excluded.text,
                etag=excluded.etag,
                last_modified=excluded.last_modified,
                fetched_at=excluded.fetched_at,
                source_status=excluded.source_status
            """,
            (reg["key"], language, url, text, etag, last_mod, now, resp.status_code),
        )

    return {"text": text, "fetched_at": now, "is_new": True, "error": None, "status": resp.status_code}


def get_cached_text(reg_key: str, language: str = "de") -> dict | None:
    init_fetcher()
    with _conn() as c:
        row = c.execute(
            "SELECT text, fetched_at FROM law_texts WHERE reg_key = ? AND language = ?",
            (reg_key, language),
        ).fetchone()
    return dict(row) if row else None
