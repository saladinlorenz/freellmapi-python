@echo off
REM FreeLLMAPI — Lanceur tout-en-un (double-clic)
REM Installe les dépendances, lance avec tray + ouvre dashboard

setlocal
cd /d "%~dp0"

:: Vérifie Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python non trouve. Installez Python 3.10+ depuis https://python.org
    pause
    exit /b 1
)

:: Vérifie pip
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] pip non disponible
    pause
    exit /b 1
)

:: Vérifie si requirements déjà satisfaits
echo [1/4] Verification dependances...
python -c "import fastapi, uvicorn, httpx, cryptography, multipart" 2>nul
if %errorlevel% neq 0 (
    echo [1/4] Installation requirements.txt...
    python -m pip install -r requirements.txt -q
    if %errorlevel% neq 0 (
        echo [WARN] Echec silencieux, reessai verbeux...
        python -m pip install -r requirements.txt
    )
) else (
    echo [1/4] Requirements deja installes - OK
)

:: Installe pystray + Pillow pour tray (si pas deja)
python -c "import pystray, PIL" 2>nul
if %errorlevel% neq 0 (
    echo [2/4] Installation tray (pystray + Pillow)...
    python -m pip install pystray Pillow -q
) else (
    echo [2/4] pystray/Pillow deja presents - OK
)

:: Génère clé encryption si absent
if not exist .env (
    echo [3/4] Creation .env avec cle de chiffrement...
    python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_hex(32))" > .env
    echo PORT=3001 >> .env
    echo HOST=0.0.0.0 >> .env
    echo FREEAPI_DB_PATH=./data/freellmapi.db >> .env
) else (
    echo [3/4] .env existe - OK
)

:: Lance avec tray + ouvre dashboard
echo [4/4] Demarrage FreeLLMAPI (tray + dashboard)...
echo.
echo ==========================================
echo  FreeLLMAPI pret !
echo  Dashboard : http://localhost:3001
echo  Icône dans les icônes cachées (bas droite)
echo  Clic droit sur l'icône -> Quitter pour arreter
echo ==========================================
echo.

:: Vérifie que le module freellm est importable
python -c "import freellm; print('[OK] module freellm importable')" 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Module freellm non trouve. Installation en mode developpement...
    python -m pip install -e . -q
    if %errorlevel% neq 0 (
        echo [ERREUR] pip install -e . echoue
        pause
        exit /b 1
    )
    echo [OK] freellm installe en mode developpement
)

:: Utilise pythonw si dispo pour sans console, sinon python
where pythonw >nul 2>&1
if %errorlevel%==0 (
    echo [INFO] Lancement avec pythonw (sans console)...
    start "" pythonw -m freellm --tray
) else (
    echo [INFO] Lancement avec python (console visible)...
    start "" python -m freellm --tray
)

:: Attend que le serveur reponde (max 15s) puis ouvre navigateur
echo [INFO] Attente du serveur (max 15s)...
for /l %%i in (1,1,30) do (
    curl -s http://localhost:3001/livez >nul 2>&1
    if %errorlevel%==0 (
        echo [OK] Serveur pret
        goto :open_browser
    )
    timeout /t 1 >nul
)
echo [WARN] Serveur pas repondu apres 15s, ouverture quand meme...
:open_browser
start "" "http://localhost:3001"

echo Lanceur termine. La fenetre peut etre fermee (l'app tourne en arriere-plan).
echo Si l'icone n'apparait pas, verifiez les icones cachées (fleche bas droite).
pause