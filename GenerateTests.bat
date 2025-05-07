@echo off
REM Script pour exécuter le générateur de cas de test en ligne de commande

if "%~1"=="" (
    echo Usage: GenerateTests.bat JIRA-ID
    echo Exemple: GenerateTests.bat PT-28
    echo.
    echo Pour lancer l'interface graphique, utilisez TestCaseGenerator.bat
    pause
    exit /b 1
)

echo Génération des cas de test pour %~1...
cd /d "%~dp0"
python run.py %~1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Une erreur s'est produite lors de la génération.
    echo.
    pause
    exit /b 1
)
echo.
pause
exit /b 0