"""ESG-Regulierungs-Check — Flask-Anwendung.

Start: python app.py   (Dev-Server, Port 5000)
Prod:  gunicorn -w 2 -b 0.0.0.0:8080 app:app
"""
from __future__ import annotations

import json
import os
import queue
import threading
from datetime import datetime

from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    session,
    stream_with_context,
    url_for,
)

import db
from i18n import (
    BRANCH_LABELS,
    GROUP_ROLE_LABELS,
    LANGUAGES,
    LEGAL_FORM_LABELS,
    LOCATION_LABELS,
    PRODUCT_CAT_LABELS,
    SITE_TYPE_LABELS,
    normalize_lang,
    t,
    t_opt,
)
from llm import analyze_streaming, profile_hash, reg_hash
from fetcher import fetch_law_text, get_cached_text
from regulations import (
    BRANCHES,
    GROUP_ROLES,
    LEGAL_FORMS,
    LOCATIONS,
    PRODUCT_CATEGORIES,
    REGULATIONS,
    SITE_TYPES,
)
from views import render_cards_html, render_csv

load_dotenv(override=True)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "esg-dev-secret-change-me")


# Reverse-Proxy Subpath: nginx sendet X-Script-Name Header,
# damit url_for() automatisch /regulierungs-check prefixed.
class PrefixMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        script_name = environ.get("HTTP_X_SCRIPT_NAME", "")
        if script_name:
            environ["SCRIPT_NAME"] = script_name
        return self.wsgi_app(environ, start_response)


app.wsgi_app = PrefixMiddleware(app.wsgi_app)

db.init_db()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _lang() -> str:
    return normalize_lang(session.get("ui_language"))


def _uid() -> int | None:
    return session.get("user_id")


def _require_login():
    if not _uid():
        return redirect(url_for("login"))
    return None


def _provider_info() -> tuple[str, str]:
    provider = (os.getenv("LLM_PROVIDER") or "ollama").lower()
    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "-")
    elif provider == "anthropic":
        model = os.getenv("CLAUDE_MODEL", "-")
    else:
        model = os.getenv("OPENAI_MODEL", "-")
    return provider, model


# Jinja2 globals
@app.context_processor
def _inject_globals():
    lang = _lang()
    return dict(
        t=t,
        t_opt=t_opt,
        lang=lang,
        LANGUAGES=LANGUAGES,
        BRANCH_LABELS=BRANCH_LABELS,
        SITE_TYPE_LABELS=SITE_TYPE_LABELS,
        LOCATION_LABELS=LOCATION_LABELS,
        LEGAL_FORM_LABELS=LEGAL_FORM_LABELS,
        GROUP_ROLE_LABELS=GROUP_ROLE_LABELS,
        PRODUCT_CAT_LABELS=PRODUCT_CAT_LABELS,
    )


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    if _uid():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    lang = _lang()
    if request.method == "POST":
        action = request.form.get("action")
        email = (request.form.get("email") or "").strip()
        pw = request.form.get("password", "")

        if action == "login":
            uid = db.verify_user(email, pw)
            if uid:
                session["user_id"] = uid
                session["user_email"] = email
                return redirect(url_for("dashboard"))
            flash(t("err_login_failed", lang), "error")

        elif action == "signup":
            pw2 = request.form.get("password2", "")
            import re
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                flash(t("err_email_invalid", lang), "error")
            elif len(pw) < 8:
                flash(t("err_pw_short", lang), "error")
            elif pw != pw2:
                flash(t("err_pw_mismatch", lang), "error")
            elif db.email_exists(email):
                flash(t("err_email_exists", lang), "error")
            else:
                uid = db.create_user(email, pw)
                session["user_id"] = uid
                session["user_email"] = email
                flash(t("ok_account_created", lang), "success")
                return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/set-language", methods=["POST"])
def set_language():
    lang = request.form.get("language", "de")
    session["ui_language"] = normalize_lang(lang)
    return redirect(request.referrer or url_for("index"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    redir = _require_login()
    if redir:
        return redir

    uid = _uid()
    lang = _lang()
    company = db.get_company(uid)
    last = db.latest_analysis(uid)
    provider, model = _provider_info()

    cards_html = ""
    if last:
        cards_html = render_cards_html(last["result"], lang)

    return render_template(
        "dashboard.html",
        company=company or {},
        last=last,
        cards_html=cards_html,
        provider=provider,
        model=model,
        BRANCHES=BRANCHES,
        SITE_TYPES=SITE_TYPES,
        LOCATIONS=LOCATIONS,
        LEGAL_FORMS=LEGAL_FORMS,
        GROUP_ROLES=GROUP_ROLES,
        PRODUCT_CATEGORIES=PRODUCT_CATEGORIES,
        reg_count=len(REGULATIONS),
    )


@app.route("/save-company", methods=["POST"])
def save_company():
    redir = _require_login()
    if redir:
        return redir

    uid = _uid()
    lang = _lang()
    f = request.form

    sites = []
    i = 0
    while f"site_type_{i}" in f:
        count = int(f.get(f"site_count_{i}", 0) or 0)
        if count > 0:
            sites.append({
                "type": f.get(f"site_type_{i}", SITE_TYPES[0]),
                "location": f.get(f"site_location_{i}", LOCATIONS[0]),
                "count": count,
            })
        i += 1

    data = {
        "name": (f.get("name") or "").strip() or None,
        "employees": int(f.get("employees") or 0),
        "employees_de": int(f.get("employees_de") or 0),
        "revenue_eur": float(f.get("revenue_eur") or 0),
        "balance_sheet_eur": float(f.get("balance_sheet_eur") or 0),
        "legal_form": f.get("legal_form", LEGAL_FORMS[0]),
        "group_role": f.get("group_role", GROUP_ROLES[0]),
        "branch": f.get("branch", BRANCHES[0]),
        "b2c": "b2c" in f,
        "listed": "listed" in f,
        "env_claims": "env_claims" in f,
        "product_categories": f.getlist("product_categories"),
        "sites": sites,
        "language": lang,
    }
    db.upsert_company(uid, data)
    flash(t("ok_saved", lang), "success")
    return redirect(url_for("dashboard"))


# ---------------------------------------------------------------------------
# Analyse (Background-Thread + Polling)
# ---------------------------------------------------------------------------
# Globaler Status-Speicher pro User (einfach, reicht für Single-VPS)
_analysis_status: dict[int, dict] = {}


def _run_analysis_bg(uid: int, profile: dict, lang: str) -> None:
    """Läuft im Background-Thread. Schreibt Fortschritt in _analysis_status."""
    status = _analysis_status[uid]
    try:
        ph = profile_hash(profile)
        cached_map = db.get_cache(uid, ph)
        total = len(REGULATIONS)
        status.update({"phase": "texts", "done": 0, "total": total, "name": ""})

        # Phase 1: Volltexte
        texts: dict[str, str] = {}
        for i, reg in enumerate(REGULATIONS, 1):
            status.update({"done": i, "name": reg["name"]})
            cached = get_cached_text(reg["key"], lang)
            if cached and cached.get("text"):
                texts[reg["key"]] = cached["text"]
                continue
            res = fetch_law_text(reg, language=lang)
            texts[reg["key"]] = res.get("text") or ""

        # Phase 2: LLM-Analyse
        cached_hits: list[dict] = []
        jobs: list[tuple[dict, str]] = []
        for reg in REGULATIONS:
            hit = cached_map.get(reg["key"])
            if hit and hit.get("reg_hash") == reg_hash(reg):
                cached_hits.append(hit["result"])
            else:
                jobs.append((reg, texts.get(reg["key"], "")))

        status.update({"phase": "analysis", "done": len(cached_hits), "total": total,
                        "cached": len(cached_hits), "new": len(jobs), "name": ""})

        q = analyze_streaming(profile, jobs, cached_hits)
        results: list[dict] = []
        done = len(cached_hits)
        while True:
            item = q.get()
            if item is None:
                break
            if not item.pop("_from_cache", False) and item.get("applies") != "error":
                rh = ""
                for reg in REGULATIONS:
                    if reg["key"] == item["key"]:
                        rh = reg_hash(reg)
                        break
                db.put_cache(uid, ph, item["key"], rh, item)
            results.append(item)
            done += 1
            status.update({"done": done, "name": item.get("name", "-")})

        # Speichern
        if any((r.get("applies") or "").lower() != "error" for r in results):
            db.save_analysis(uid, results)

        status.update({"phase": "done", "done": total, "total": total})

    except Exception as e:
        status.update({"phase": "error", "error": str(e)})


@app.route("/run-analysis")
def run_analysis_page():
    redir = _require_login()
    if redir:
        return redir

    uid = _uid()
    lang = _lang()
    company = db.get_company(uid)
    if not company or not company.get("employees"):
        return redirect(url_for("dashboard"))

    # Analyse im Background-Thread starten
    profile = {**company, "language": lang}
    _analysis_status[uid] = {"phase": "starting", "done": 0, "total": len(REGULATIONS), "name": ""}
    t_thread = threading.Thread(target=_run_analysis_bg, args=(uid, profile, lang), daemon=True)
    t_thread.start()

    return render_template("analysis.html")


@app.route("/api/analysis-status")
def analysis_status_api():
    uid = _uid()
    if not uid:
        return json.dumps({"phase": "error", "error": "not authenticated"}), 401
    status = _analysis_status.get(uid, {"phase": "idle"})
    return Response(json.dumps(status, ensure_ascii=False), mimetype="application/json")


# ---------------------------------------------------------------------------
# Vollbild + CSV
# ---------------------------------------------------------------------------
@app.route("/fullscreen")
def fullscreen():
    uid = request.args.get("uid", type=int) or _uid()
    if not uid:
        return "No user", 400
    last = db.latest_analysis(uid)
    if not last:
        return render_template("fullscreen.html", cards_html="", last=None)
    lang = normalize_lang(request.args.get("lang") or _lang())
    cards_html = render_cards_html(last["result"], lang)
    return render_template("fullscreen.html", cards_html=cards_html, last=last, lang=lang)


@app.route("/download-csv")
def download_csv():
    uid = _uid()
    if not uid:
        return redirect(url_for("login"))
    last = db.latest_analysis(uid)
    if not last:
        return "No results", 404
    lang = _lang()
    csv_bytes = render_csv(last["result"], lang)
    fname = f"esg_analyse_{datetime.now():%Y%m%d_%H%M}.csv"
    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
