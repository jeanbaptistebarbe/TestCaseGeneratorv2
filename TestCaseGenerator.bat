@echo off
REM Script de lancement pour TestCaseGenerator v2

echo Démarrage de TestCaseGenerator...
cd /d "%~dp0"
python interface\launch_jira.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Une erreur s'est produite lors du démarrage.
    echo Assurez-vous que Python est installé et que les dépendances sont configurées.
    echo.
    pause
    exit /b 1
)
exit /b 0