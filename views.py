"""HTML-Generierung für Regulierungskarten + CSV-Export.

Kein Streamlit mehr — reines HTML/CSS für Flask-Templates.
"""
from __future__ import annotations

import csv
import io
import re
from html import escape

APPLIES_ORDER = {"error": 0, "ja": 1, "moeglich": 2, "nein": 3}

I18N = {
    "de": {
        "metric_yes": "Greift",
        "metric_maybe": "Möglich / zu prüfen",
        "metric_no": "Nicht einschlägig",
        "applies_label": {"ja": "GREIFT", "moeglich": "MÖGLICH", "nein": "NICHT EINSCHLÄGIG", "error": "FEHLER"},
        "reason": "Begründung",
        "reason_missing": "Keine Begründung verfügbar.",
        "passage": "Greifende Stelle",
    },
    "en": {
        "metric_yes": "Applies",
        "metric_maybe": "Possible / to verify",
        "metric_no": "Not applicable",
        "applies_label": {"ja": "APPLIES", "moeglich": "POSSIBLE", "nein": "NOT APPLICABLE", "error": "ERROR"},
        "reason": "Reason",
        "reason_missing": "No justification available.",
        "passage": "Triggering passage",
    },
    "es": {
        "metric_yes": "Aplica",
        "metric_maybe": "Posible / a verificar",
        "metric_no": "No aplicable",
        "applies_label": {"ja": "APLICA", "moeglich": "POSIBLE", "nein": "NO APLICABLE", "error": "ERROR"},
        "reason": "Justificación",
        "reason_missing": "Sin justificación disponible.",
        "passage": "Pasaje relevante",
    },
    "fr": {
        "metric_yes": "S'applique",
        "metric_maybe": "Possible / à vérifier",
        "metric_no": "Non applicable",
        "applies_label": {"ja": "S'APPLIQUE", "moeglich": "POSSIBLE", "nein": "NON APPLICABLE", "error": "ERREUR"},
        "reason": "Justification",
        "reason_missing": "Aucune justification disponible.",
        "passage": "Passage pertinent",
    },
    "it": {
        "metric_yes": "Si applica",
        "metric_maybe": "Possibile / da verificare",
        "metric_no": "Non applicabile",
        "applies_label": {"ja": "SI APPLICA", "moeglich": "POSSIBILE", "nein": "NON APPLICABILE", "error": "ERRORE"},
        "reason": "Motivazione",
        "reason_missing": "Nessuna motivazione disponibile.",
        "passage": "Passaggio rilevante",
    },
    "zh": {
        "metric_yes": "适用",
        "metric_maybe": "可能 / 需核实",
        "metric_no": "不适用",
        "applies_label": {"ja": "适用", "moeglich": "可能", "nein": "不适用", "error": "错误"},
        "reason": "理由",
        "reason_missing": "暂无理由说明。",
        "passage": "相关条款",
    },
}

BADGE_STYLES = {
    "ja": ("background:#1f4e3d;color:white;", "✓"),
    "moeglich": ("background:#d4a017;color:white;", "?"),
    "nein": ("background:#6b6b6b;color:white;", "—"),
    "error": ("background:#991b1b;color:white;", "✕"),
}


_PASSAGE_MAX_CHARS = 280


def _shorten_passage(text: str) -> str:
    """Kurzform fuer das 'Greifende Stelle'-Feld.

    Manche Modelle liefern ganze Paragraphen-Listen statt einem kurzen Zitat.
    Wir nehmen den ersten Satz oder die ersten 280 Zeichen; der Rest wird
    mit … abgeschnitten.
    """
    t = (text or "").strip()
    if not t:
        return ""
    # Zeilenumbrueche und Aufzaehlungspunkte entfernen
    t = re.sub(r"\s*[\r\n]+\s*[-*•]?\s*", " ", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    if len(t) <= _PASSAGE_MAX_CHARS:
        return t
    cut = t[:_PASSAGE_MAX_CHARS]
    # Wenn moeglich nach Satzende kappen
    dot = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if dot > _PASSAGE_MAX_CHARS // 2:
        return cut[:dot + 1].rstrip() + " …"
    return cut.rstrip() + " …"


def _card_html(r: dict, lang_dict: dict) -> str:
    a = r["applies"]
    bg, icon = BADGE_STYLES.get(a, ("background:#999;color:white;", "·"))
    label = lang_dict["applies_label"].get(a, a.upper())
    name = escape(r["name"])
    full = escape(r["full_name"])
    url = escape(r["url"])
    article = escape(r.get("article") or "")
    passage = escape(_shorten_passage(r.get("passage") or ""))
    reason_raw = (r.get("reason") or "").strip()
    reason = escape(reason_raw) if reason_raw else f'<em style="color:#aaa;">{escape(lang_dict["reason_missing"])}</em>'
    nr = r.get("nr", "")
    return f"""
<div class="reg-card">
  <div class="reg-card-header">
    <span class="badge" style="{bg}">{icon} {label}</span>
    <span class="reg-nr">Nr. {nr}</span>
    <a href="{url}" target="_blank" rel="noopener" class="reg-name">{name}</a>
    <span class="reg-full">— {full}</span>
  </div>
  <div class="reg-reason"><strong>{escape(lang_dict['reason'])}:</strong> {reason}</div>
  <div class="reg-passage"><strong>{escape(lang_dict['passage'])}:</strong> <em>{article}{': ' if article else ''}{passage}</em></div>
</div>"""


def _metrics_html(shown: list[dict], lang_dict: dict) -> str:
    yes = sum(1 for r in shown if r["applies"] == "ja")
    maybe = sum(1 for r in shown if r["applies"] == "moeglich")
    no = sum(1 for r in shown if r["applies"] == "nein")
    return f"""
<div class="metrics">
  <div class="metric metric-yes"><div class="metric-value">{yes}</div><div class="metric-label">{escape(lang_dict['metric_yes'])}</div></div>
  <div class="metric metric-maybe"><div class="metric-value">{maybe}</div><div class="metric-label">{escape(lang_dict['metric_maybe'])}</div></div>
  <div class="metric metric-no"><div class="metric-value">{no}</div><div class="metric-label">{escape(lang_dict['metric_no'])}</div></div>
</div>"""


def render_cards_html(results: list[dict], language: str = "de") -> str:
    """Generiert das komplette Ergebnis-HTML (Metriken + Karten)."""
    lang_dict = I18N.get(language, I18N["de"])
    shown = [r for r in results if (r.get("applies") or "").lower() in APPLIES_ORDER]
    shown.sort(key=lambda r: (APPLIES_ORDER.get((r.get("applies") or "").lower(), 9), r["nr"]))

    if not shown:
        return '<p class="no-results">—</p>'

    parts = [_metrics_html(shown, lang_dict)]
    parts.extend(_card_html(r, lang_dict) for r in shown)
    return "\n".join(parts)


def render_csv(results: list[dict], language: str = "de") -> bytes:
    """Generiert CSV als UTF-8-BOM-Bytes."""
    lang_dict = I18N.get(language, I18N["de"])
    shown = [r for r in results if (r.get("applies") or "").lower() in APPLIES_ORDER]
    shown.sort(key=lambda r: (APPLIES_ORDER.get((r.get("applies") or "").lower(), 9), r["nr"]))

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Status", "Nr.", "Regulierung", "Bezeichnung",
                     lang_dict["reason"], lang_dict["passage"], "URL"])
    for r in shown:
        writer.writerow([
            lang_dict["applies_label"].get(r["applies"], r["applies"].upper()),
            r["nr"],
            r["name"],
            r["full_name"],
            r.get("reason", ""),
            f'{r.get("article","")}: {r.get("passage","")}',
            r["url"],
        ])
    return ("\ufeff" + buf.getvalue()).encode("utf-8")
