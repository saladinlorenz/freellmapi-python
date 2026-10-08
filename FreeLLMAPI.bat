@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo  FreeLLMAPI - Lancement du serveur
echo ==========================================
echo.

:: 1. Verification de Python
echo [1/7] Verification de Python...
python --version >nul 2>&1
if errorlevel 1 goto no_python
echo [OK] Python installe.

:: 2. Verification du port 3001
echo [2/7] Verification du port 3001...
netstat -ano | findstr /R /C:":3001 .*LISTENING" >nul 2>&1
if not errorlevel 1 goto port_busy
echo [OK] Port 3001 libre.

:: 3. Creation et test d'ecriture du dossier data
echo [3/7] Verification du dossier data...
if not exist "data" mkdir "data" 2>nul
if not exist "data\logs" mkdir "data\logs" 2>nul
python -c "import pathlib; pathlib.Path('data/.writetest').write_text('ok')" 2>nul
if errorlevel 1 goto data_fail
del /q "data\.writetest" >nul 2>&1
echo [OK] data/ accessible.

:: 4. Creation ou mise a jour du fichier .env
echo [4/7] Verification du fichier .env...
if exist ".env" goto env_exists
echo [INFO] Creation du fichier .env...
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_hex(32))" > ".env"
if errorlevel 1 goto env_fail
>>".env" echo PORT=3001
>>".env" echo HOST=0.0.0.0
>>".env" echo FREEAPI_DB_PATH=./data/freeapi.db
goto env_done
:env_exists
findstr /C:"ENCRYPTION_KEY" ".env" >nul 2>&1
if not errorlevel 1 goto env_done
echo [INFO] Ajout de ENCRYPTION_KEY dans .env...
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_hex(32))" >> ".env"
:env_done
echo [OK] .env pret.

:: 5. Verification des dependances requises
echo [5/7] Verification des dependances...
python -c "import fastapi, uvicorn, httpx, cryptography" 2>nul
if not errorlevel 1 goto deps_ok
echo [INFO] Installation des dependances - requirements.txt...
python -m pip install -r requirements.txt
if errorlevel 1 goto deps_fail
:deps_ok
echo [OK] Dependances requises.

:: 6. Verification du module freellm
echo [6/7] Verification du module freellm...
python -c "import freellm" 2>nul
if not errorlevel 1 goto module_ok
echo [INFO] Installation de freellm en mode developpement...
python -m pip install -e .
if errorlevel 1 goto deps_fail
:module_ok
echo [OK] Module freellm.

:: 7. Dependances de la tray (optionnel)
echo [7/7] Verification des dependances de la tray...
set "TRAY_FLAG=--tray"
python -c "import pystray, PIL" 2>nul
if not errorlevel 1 goto tray_ok
echo [INFO] Installation de pystray et Pillow...
python -m pip install pystray Pillow -q 2>nul
python -c "import pystray, PIL" 2>nul
if not errorlevel 1 goto tray_ok
echo [WARN] Tray indisponible - lancement sans tray.
set "TRAY_FLAG=--no-tray"
:tray_ok

:: 8. Choix de l'interpreteur (pythonw sans console, sinon python)
where pythonw >nul 2>&1
if errorlevel 1 goto use_python
set "PY_CMD=pythonw"
goto launch
:use_python
set "PY_CMD=python"
:launch

:: 9. Lancement de FreeLLMAPI
echo [INFO] Lancement de FreeLLMAPI en arriere-plan...
start "" %PY_CMD% -m freellm %TRAY_FLAG%

:: 10. Attente de disponibilite du serveur (poll /livez)
echo [INFO] Attente du demarrage du serveur - poll /livez...
set /a TRIES=0
:poll
ping -n 2 127.0.0.1 >nul
curl -s http://localhost:3001/livez 2>nul | findstr /C:"ok" >nul 2>&1
if not errorlevel 1 goto ready
set /a TRIES+=1
if %TRIES% LSS 15 goto poll
goto failed

:ready
echo.
echo ==========================================
echo  FreeLLMAPI est pret !
echo  Dashboard : http://localhost:3001
echo  Icone active dans la zone de notification.
echo ==========================================
echo [INFO] Ouverture de http://localhost:3001 dans le navigateur...
start "" "http://localhost:3001"
ping -n 3 127.0.0.1 >nul
exit /b 0

:port_busy
echo [INFO] Le port 3001 est deja utilise - serveur deja lance ?
echo [INFO] Ouverture de http://localhost:3001 dans le navigateur...
start "" "http://localhost:3001"
ping -n 3 127.0.0.1 >nul
exit /b 0

:no_python
echo [ERREUR] Python introuvable.
echo Installez Python 3.10+ depuis https://python.org avec l'option Add to PATH.
pause
exit /b 1

:data_fail
echo [ERREUR] Dossier data inaccessible en ecriture.
pause
exit /b 1

:env_fail
echo [ERREUR] Impossible de creer le fichier .env.
pause
exit /b 1

:deps_fail
echo [ERREUR] Impossible d'installer les dependances requises.
pause
exit /b 1

:failed
echo.
echo [ERREUR] Le serveur n'a pas repondu apres 15 secondes.
echo Essayez de le lancer manuellement pour voir les erreurs :
echo   python -m freellm
echo.
pause
exit /b 1
