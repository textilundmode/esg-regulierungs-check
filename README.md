# ESG-Regulierungs-Check

Streamlit-Web-App, die prueft, welche ESG-/CSR-Regulierungen fuer ein Unternehmen gelten.
**Volltext-basierte Analyse** — laedt die Originaltexte der Gesetze, cached sie lokal
und befragt einen LLM gegen Profil + echten Gesetzestext. Ergebnis: Liste mit Begruendung,
Zitat aus dem Volltext und direktem Link.

## Schnellstart

Doppelklick auf `start.bat`. Beim ersten Lauf werden venv angelegt, Abhaengigkeiten
installiert und `.env` im Editor geoeffnet (Konfiguration vornehmen, speichern, erneut starten).

## LLM-Provider

### Default: Google AI Studio Free Tier (empfohlen)

Kostenfrei, plattformunabhaengig, keine Hardware-Voraussetzungen, 1500 Requests/Tag.

1. Kostenlosen API-Key holen: https://aistudio.google.com/apikey
2. In `.env` eintragen:
   ```
   LLM_PROVIDER=openai
   OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
   OPENAI_API_KEY=AIza...
   OPENAI_MODEL=gemini-2.5-flash
   ```

### Alternative Provider

Der `openai`-Provider akzeptiert ueber `OPENAI_BASE_URL` jeden OpenAI-kompatiblen
Endpoint — OpenRouter (inkl. Gemma 4), Alibaba Qwen Cloud, Together AI, Groq usw.
Konkrete Beispiele in `.env.example`.

Alternativ `LLM_PROVIDER=anthropic` fuer Claude oder `LLM_PROVIDER=ollama` fuer
lokalen Offline-Betrieb (Gemma 4 E2B laeuft auch auf CPU, ~30-60 Min pro
Komplett-Check).

## Setup manuell

```bash
cd esg_app
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # dann Provider-Konfig anpassen
streamlit run app.py
```

## Bedienung

1. **Registrieren** (E-Mail + Passwort). Daten liegen lokal in `data/esg.db`.
2. **Stammdaten** ausfuellen: Unternehmensname, Mitarbeiterzahl, Umsatz, Bilanzsumme,
   Rechtsform, Konzernstruktur, Branche, B2C/Kapitalmarkt/Umweltaussagen,
   Produktkategorien (Mehrfachauswahl), Standorte.
3. **„Jetzt pruefen"** klicken. Ablauf:
   - Schritt 1: Gesetzestexte werden per HTTP geladen/aktualisiert (ETag-basiert, inkrementell)
   - Schritt 2: LLM analysiert je Regulierung Profil + Volltext → JSON mit applies/reason/passage
4. **Ergebnistabelle** zeigt nur einschlaegige oder moeglicherweise einschlaegige Regulierungen,
   sortiert JA → MOEGLICH. Regulierungsname selbst ist Link zum Originaltext. CSV-Export vorhanden.
5. **Cache:** Bei unveraendertem Profil werden gespeicherte Ergebnisse beim zweiten Klick
   instant angezeigt (kein LLM-Call).

## Datenbank

Eine SQLite-Datei (`data/esg.db`) mit Tabellen:
- `users` — Login (bcrypt)
- `companies` — Stammdaten pro User
- `analyses` — Historie der Checks
- `analysis_cache` — (user_id, profile_hash, reg_key) → LLM-Ergebnis
- `law_texts` — Volltexte der Gesetze mit ETag/Last-Modified fuer inkrementelle Updates

## Architektur

- `app.py` — Streamlit UI, Login, Stammdaten, Orchestration, Ergebnistabelle
- `db.py` — SQLite (Schema, Migration, CRUD), bcrypt
- `fetcher.py` — HTTP-Download von Gesetzestexten, HTML/PDF-Extraktion, Cache mit ETag
- `llm.py` — Provider-Abstraktion (Ollama/Anthropic/OpenAI), Volltext-Prompt, Retry/429-Handling
- `regulations.py` — 23 Regulierungen + Auswahllisten (Branchen, Rechtsformen, Produkte)

## Die 23 Regulierungen

CSDDD, LkSG, EUDR, FLR, CSRD, CSRD-DE, ESRS, NFRD, CSR-RUG, Taxonomie-VO, SFDR,
ESG-Rating-VO, Whistleblower-RL, HinSchG, Right to Repair, Oekodesign-VO, PPWR,
Konfliktmineralien-VO, MinRohSorgG, EU-Umweltstrafrechts-RL, EmpCo, Green Claims (Entwurf),
Omnibus I.

## Hinweise

- Die Analyse ist eine **qualifizierte Einschaetzung**, keine Rechtsberatung.
- Bei Regulierungen mit PDF-Quelle (CSRD-DE) ist die Textextraktion naeherungsweise.
- `FULLTEXT_MAX_CHARS` in `.env` kuerzt den an den LLM geschickten Text. Senken
  bei knappem Kontext-Fenster (z.B. Ollama mit kleinem `num_ctx`).
