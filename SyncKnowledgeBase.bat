@echo off
REM Script pour synchroniser la base de connaissances

echo Synchronisation de la base de connaissances...
cd /d "%~dp0"
python scripts\sync_knowledge_base.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Une erreur s'est produite lors de la synchronisation.
    echo.
    pause
    exit /b 1
)
echo.
echo Synchronisation terminée avec succès!
echo.
pause
exit /b 0