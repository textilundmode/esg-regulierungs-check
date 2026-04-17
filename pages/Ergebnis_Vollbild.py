"""Vollbild-Ansicht des letzten Analyse-Ergebnisses.

Wird vom Hauptdashboard über `/Ergebnis_Vollbild?uid=<id>&lang=<code>` in einem
neuen Tab geöffnet. Da Streamlit-Sessions nicht zwischen Tabs geteilt werden,
kommen User-ID und Sprache per Query-Parameter rein.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Hauptordner in PYTHONPATH aufnehmen, damit db/views/i18n importierbar sind
sys.path.insert(0, str(Path(__file__).parent.parent))

import db
from i18n import normalize_lang, t
from views import render_results

load_dotenv(override=True)
db.init_db()

st.set_page_config(page_title="ESG-Ergebnis Vollbild", page_icon="📋", layout="wide")
st.markdown(
    """
    <style>
      .main .block-container { padding-top: 1rem; max-width: 100% !important; padding-bottom: 2.5rem; }
      .disclaimer-top {
        color: #8b0000;
        font-style: italic;
        font-size: 13px;
        text-align: left;
        margin: 0 0 12px 0;
        padding: 4px 0;
        letter-spacing: 0.2px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sprache: erst Query-Param, dann Session, dann Default
lang_param = st.query_params.get("lang")
lang = normalize_lang(lang_param or st.session_state.get("ui_language"))

# Disclaimer ganz oben links
st.markdown(
    f'<div class="disclaimer-top">⚠ {t("disclaimer", lang)}</div>',
    unsafe_allow_html=True,
)

uid_str = st.query_params.get("uid")
if not uid_str:
    st.error(t("fullscreen_err_nouser", lang))
    st.stop()

try:
    uid = int(uid_str)
except (TypeError, ValueError):
    st.error(t("fullscreen_err_uid", lang))
    st.stop()

last = db.latest_analysis(uid)
if not last:
    st.info(t("fullscreen_no_result", lang))
    st.stop()

company = db.get_company(uid) or {}
# Darstellungssprache: Query-Param hat Vorrang vor gespeicherter Company-Sprache
display_lang = normalize_lang(lang_param or company.get("language") or lang)

st.title(t("fullscreen_title", display_lang))
st.caption(f"{t('fullscreen_status', display_lang)}: {last['created_at'][:19].replace('T', ' ')}")
render_results(last["result"], language=display_lang)
