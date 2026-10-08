@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo  FreeLLMAPI - Arret du serveur
echo ==========================================

:: 1. Arret via le module freellm (lit data/freellm.pid)
python -m freellm --stop >nul 2>&1

:: 2. Nettoyage de secours si le port 3001 reste occupe
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /R /C:":3001 .*LISTENING"') do (
    echo Fermeture du processus PID %%a sur le port 3001...
    taskkill /PID %%a /F >nul 2>&1
)

echo [OK] Serveur arrete.
ping -n 3 127.0.0.1 >nul
exit /b 0
