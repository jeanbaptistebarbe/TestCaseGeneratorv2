@echo off
REM Script d'installation pour TestCaseGenerator v2

echo Installation des dépendances pour TestCaseGenerator v2...
cd /d "%~dp0"

REM Vérifier si Python est installé
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python n'est pas installé ou n'est pas dans le PATH.
    echo Veuillez installer Python 3.8 ou supérieur depuis https://www.python.org/downloads/
    echo et cocher l'option "Add Python to PATH" durant l'installation.
    pause
    exit /b 1
)

REM Créer les dossiers nécessaires s'ils n'existent pas
echo Création des répertoires nécessaires...
if not exist "output" mkdir output
if not exist "output\logs" mkdir output\logs
if not exist "output\backup" mkdir output\backup

REM Installer les dépendances
echo Installation des packages requis...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo Une erreur s'est produite lors de l'installation des dépendances.
    pause
    exit /b 1
)

echo.
echo Installation terminée avec succès!
echo Vous pouvez maintenant lancer l'application avec TestCaseGenerator.bat
echo.
pause
exit /b 0