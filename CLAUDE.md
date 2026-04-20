# ESG-Regulierungs-Check — Projekt-Memo für Claude Code

> **Dieses Dokument ist die Quelle der Wahrheit über den aktuellen Stand.**
> Beim Sitzungsstart hier zuerst hineinschauen, dann gezielt in den Code.

---

## Aktueller stabiler Stand

- **Live-URL:** https://schuckert.cloud/regulierungs-check
- **Stabiler Commit:** `40f4941` (branch `main`)
- **Git-Tag:** `stable-2026-04-20`
- **Stand dieses Dokuments:** 2026-04-20

---

## Was funktioniert (Feature-Inventar)

| Feature | Ort | Status |
|---|---|---|
| Login / Registrierung (bcrypt, SQLite) | `app.py`, `db.py` | ✅ |
| Stammdaten-Formular (inkl. Standorte, Produktkategorien) | `templates/dashboard.html` | ✅ |
| LLM-Analyse über 23 Regulierungen (Volltext + Guidelines) | `app.py` `_run_analysis_bg`, `llm.py` | ✅ |
| Result-Cache (Profil-Hash + Reg-Hash → Ergebnis) | `db.py` `analysis_cache` | ✅ |
| Gesetzestext-Cache mit ETag / Last-Modified | `fetcher.py` `law_texts` | ✅ |
| CSV-Export | `/download-csv` | ✅ |
| Fullscreen-Ansicht Ergebnisse | `/fullscreen` | ✅ |
| **Regulierungsliste** (3-spaltig: Reg / Guidelines / Quelle+Stand) | `/regulierungsliste`, `templates/regulierungsliste.html` | ✅ |
| **textil+mode-Logo oben links** (verlinkt textil-mode.de) | `templates/base.html`, `static/images/tum-logo.svg` | ✅ |
| **Dunkelgraue Seitenränder** (`#2b2b2b` außerhalb des 1140px-Containers) | `templates/base.html` | ✅ |
| **Footer-Hinweis** ("Claude Code + OpenAI Codex") unten rechts als `<details>` | `templates/base.html` | ✅ |
| i18n (DE / EN / ES / FR / IT / ZH) | `i18n.py` | ✅ |

---

## Architektur (Deployment-Kette)

```
Browser
  └─> https://schuckert.cloud/regulierungs-check/…
        └─> nginx (auf VPS) — strippt `/regulierungs-check` Prefix
              └─> localhost:8082 (Docker host port)
                    └─> Container esg-regulierungs-check (interne Port 8080)
                          └─> Gunicorn (1 Worker, 8 Threads) → Flask `app:app`
```

**Reverse-Proxy-Prefix-Handling** (wichtig!): nginx setzt den HTTP-Header
`X-Script-Name: /regulierungs-check`. `app.py` hat eine `PrefixMiddleware`, die
diesen Header liest und `environ["SCRIPT_NAME"]` setzt — dadurch produziert
Flask's `url_for()` automatisch Pfade mit dem Prefix.

---

## Hosting (Hostinger VPS)

- **Hoster:** Hostinger
- **VPS-Plan:** KVM 4 (Ubuntu 24.04, Docker)
- **VPS-ID:** 1400170 · `srv1400170.hstgr.cloud` · IP `187.77.88.67`
- **Docker Manager:** https://hpanel.hostinger.com/vps/1400170/docker-manager
- **Projektname dort:** `esg-regulierungs-check`
- **Container-Name:** `esg-regulierungs-check`
- **Port-Mapping:** `8082:8080` (host:container)
- **Volume:** `esg-data` → `/app/data` (SQLite-DB persistiert hier)
- **Compose-Datei im Hostinger-UI** enthält Secrets (API-Keys), NICHT ident mit der Repo-Kopie editieren.

---

## CI/CD

- **Repo:** `textilundmode/esg-regulierungs-check` (privat)
- **Workflow:** `.github/workflows/docker-build.yml`
  - Trigger: push auf `main` oder `master`
  - Baut Docker-Image aus `Dockerfile`
  - Pusht nach `ghcr.io/textilundmode/esg-regulierungs-check:latest`
  - Dauer: typischerweise 1-2 Min (Build-Cache vorhanden)

### Deploy-Prozedur (nach Code-Änderung)

1. `git add <geänderte Dateien>` — **kein** `git add -A` (vermeidet versehentliches Einchecken von Secrets / Scratch-Dateien)
2. `git commit -m "…"`
3. `git push origin main`
4. Warten auf Build-Erfolg: https://github.com/textilundmode/esg-regulierungs-check/actions
5. Hostinger → Docker Manager → Projekt `esg-regulierungs-check` → **Verwalten** → **Bereitstellen**
6. Nach ~15 s testen: https://schuckert.cloud/regulierungs-check

> ⚠️ **Dockerfile muss `COPY static/ static/` und `COPY templates/ templates/` enthalten.** Sonst fehlen Assets im Image. Beide sind drin (Stand Tag `stable-2026-04-20`).

---

## Rollback auf diesen stabilen Stand

Falls die App nach einer Änderung nicht mehr läuft:

```bash
# Option A: Lokal auf den stabilen Stand zurück und Force-Push (ZERSTÖRT neuere Commits!)
git fetch origin
git reset --hard stable-2026-04-20
git push origin main --force-with-lease

# Option B: Neuen Commit bauen, der den Stand des Tags wiederherstellt (non-destructive)
git revert <bad-commit-sha>  # oder gezielt
# oder:
git checkout -b rollback-2026-04-20 stable-2026-04-20
git push origin rollback-2026-04-20
# dann PR/Merge nach main

# Nach dem Push:
# → GitHub Actions baut neu (~2 min)
# → Hostinger → Verwalten → Bereitstellen
```

---

## LLM-Konfiguration

Aktive Konfiguration (Hostinger `docker-compose.hostinger.yml`, Environment):

| Variable | Wert |
|---|---|
| `LLM_PROVIDER` | `openai` (OpenAI-kompatibles Interface) |
| `OPENAI_BASE_URL` | `https://openrouter.ai/api/v1` (OpenRouter-Proxy) |
| `OPENAI_MODEL` | `nvidia/nemotron-3-super-120b-a12b:free` |
| `LLM_CONCURRENCY` | `4` |
| `LLM_RPM` | `18` (Rate-Limit OpenRouter Free-Tier) |
| `FULLTEXT_MAX_CHARS` | `40000` |

**Weitere Keys gesetzt aber aktuell inaktiv** (stehen als Fallback bereit):
- `ANTHROPIC_API_KEY` + `CLAUDE_MODEL=claude-sonnet-4-6` → wird genutzt wenn `LLM_PROVIDER=anthropic`

Provider-Switch: Im Hostinger-Compose-YAML `LLM_PROVIDER` ändern → Bereitstellen.

---

## Daten-/Content-Quellen

### Regulierungen — statische Metadaten (`regulations.py`)

- `REGULATIONS` — 23 Einträge mit `key`, `name`, `full_name`, `url`, `text_url`, `scope`, `criteria`, `key_article`
- `GUIDELINES_BY_REG_KEY` — je Regulierung eine Liste kuratierter offizieller Leitlinien (EU-Kommission, BAFA, EFRAG, ESMA, IDW, BfJ, DRSC)
- `PUBLISHED_BY_REG_KEY` — Veröffentlichungsdatum je Reg (OJ-Datum bzw. BGBl.-Datum), Format `DD.MM.YYYY`

Wenn ein Datum / eine Guideline-URL aktualisiert werden muss → direkt in `regulations.py` editieren, kein DB-Migration nötig.

### Dynamische Daten (Cache, SQLite in `/app/data/esg.db`)

- `users`, `companies`, `analyses`, `analysis_cache`, `law_texts` (Volltext + ETag + Last-Modified + fetched_at)
- Guidelines werden ebenfalls in `law_texts` gespeichert mit `reg_key` = `GUIDE:<sha256-prefix>` (siehe `fetcher.py` `_guideline_key`).

---

## Schlüsseldateien (was wo lebt)

| Datei | Zweck |
|---|---|
| `app.py` | Flask-Routen, Login, Analyse-Orchestrierung, PrefixMiddleware |
| `llm.py` | LLM-Provider-Abstraktion (openai / ollama / anthropic / google), Prompt, Rate-Limit |
| `fetcher.py` | HTTP-Download von Gesetzes-/Guideline-Texten, HTML/PDF-Extraktion, ETag-Cache |
| `regulations.py` | 23 Regulierungen + Guidelines-Map + Veröffentlichungsdaten + Auswahllisten |
| `i18n.py` | Übersetzungen (6 Sprachen) |
| `db.py` | SQLite-Schema, Migrationen, Cache-Zugriff |
| `views.py` | Card/CSV-Renderer |
| `templates/base.html` | Layout, CSS, Logo, Topbar, Footer |
| `templates/dashboard.html` | Hauptseite (Stammdaten + "Jetzt prüfen" + "Regulierungsliste"-Button) |
| `templates/regulierungsliste.html` | Tabelle aller 23 Regs + Guidelines + Stand |
| `templates/login.html`, `fullscreen.html`, `analysis.html` | Auth, Fullscreen, Progress-Page |
| `static/images/tum-logo.svg` | textil+mode-Logo |
| `Dockerfile` | Python 3.12-slim + Gunicorn; **muss `static/` und `templates/` kopieren** |
| `docker-compose.hostinger.yml` | Compose-Template (enthält API-Keys — live auf Hostinger editiert) |
| `.github/workflows/docker-build.yml` | Build-Push nach ghcr.io |

---

## Verifikations-Checks (smoke-tests nach Deploy)

1. https://schuckert.cloud/regulierungs-check → Login-Seite lädt, Logo oben links sichtbar, Footer "© 2026 · Alle Rechte vorbehalten".
2. Nach Login: Dashboard mit Button "Regulierungsliste" oben rechts neben "Jetzt prüfen".
3. https://schuckert.cloud/regulierungs-check/regulierungsliste → Tabelle mit 23 Zeilen, Stand im Format `DD.MM.YYYY`, Guidelines klickbar.
4. Footer unten rechts: `<details>` "Hinweis" → auf Klick Popover mit Claude-Code-/Codex-Text.

---

## Konventionen für Claude Code

- **Never commit** die `_*.txt`-Scratch-Dateien (bash-output-Captures); sie liegen im Repo-Root.
- **Never commit** `.playwright-mcp/`, `Bugreport/`, `.claude/`.
- **Nur explizit geänderte Dateien stagen**, kein `git add -A`.
- Syntax-Check vor Commit: `./.venv/Scripts/python.exe -m py_compile app.py fetcher.py regulations.py llm.py i18n.py`.
- Feature-Arbeit: neuer Commit, neuer Tag, wenn wieder "stabil".

---

## Offene Punkte / Ideen

- Einige Guideline-URLs sind Landing-Pages (nicht direkt der Leitfaden-PDF). Feintuning später.
- NVIDIA Nemotron Free-Tier hat harte Limits; bei Bedarf auf Claude Sonnet 4.6 umschalten (siehe LLM-Konfiguration).
- `README.md` ist teilweise veraltet (erwähnt noch Streamlit). CLAUDE.md ist der aktuelle Stand.
