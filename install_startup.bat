@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo  FreeLLMAPI - Configuration demarrage Windows
echo ==========================================

python -c "from freellm.tray import set_autostart; ok = set_autostart(True); exit(0 if ok else 1)"
if not errorlevel 1 goto ok
echo [ERREUR] Impossible de configurer le demarrage automatique.
pause
exit /b 1

:ok
echo [OK] FreeLLMAPI ajoute au dossier Demarrage de Windows.
echo Il se lancera en arriere-plan a chaque ouverture de session.
pause
exit /b 0
