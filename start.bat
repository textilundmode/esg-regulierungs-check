@echo off
setlocal

cd /d "%~dp0"

echo [Cleanup] Beende ggf. laufende Streamlit-Prozesse...
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *streamlit*" /NH 2^>nul ^| find "python.exe"') do taskkill /PID %%i /F >nul 2>&1
REM Fallback: jeder python.exe der Streamlit heisst
wmic process where "name='python.exe' and commandline like '%%streamlit%%'" delete >nul 2>&1

if not exist ".venv" (
    echo [Setup] Erstelle virtuelle Umgebung...
    python -m venv .venv
    if errorlevel 1 goto :error
    call ".venv\Scripts\activate.bat"
    echo [Setup] Installiere Abhaengigkeiten...
    pip install -r requirements.txt
    if errorlevel 1 goto :error
) else (
    call ".venv\Scripts\activate.bat"
    REM Stelle sicher, dass neue Deps drin sind (schnell wenn schon installiert)
    pip install -q -r requirements.txt
)

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo.
    echo [!] .env wurde angelegt. Bitte Provider-Konfig eintragen und erneut starten.
    notepad .env
    goto :eof
)

echo [Start] Oeffne Streamlit...
streamlit run app.py
goto :eof

:error
echo.
echo [Fehler] Setup fehlgeschlagen. Pruefe, ob Python 3.10+ installiert ist.
pause
