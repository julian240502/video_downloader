@echo off
cls

echo.
echo ========================================
echo    VIDEO DOWNLOADER
echo    INSTALLATION (une fois seulement)
echo ========================================
echo.

REM Verifier Python
py --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR : Python n'est pas installe !
    echo.
    echo Etapes :
    echo  1. Aller sur https://python.org/downloads/
    echo  2. Telecharger Python 3.10 ou plus
    echo  3. COCHER "Add Python to PATH"
    echo  4. Relancer ce fichier apres
    echo.
    pause
    exit /b 1
)

echo OK - Python trouve
echo.

REM Creer venv (une seule fois)
if exist "venv\" (
    echo OK - Environnement virtuel existe
    echo.
) else (
    echo Creation de l'environnement virtuel...
    py -m venv venv
    if errorlevel 1 (
        echo ERREUR : Impossible de creer venv
        pause
        exit /b 1
    )
    echo OK - Environnement virtuel cree
    echo.
)

REM Installer les dependances
echo Installation des dependances...
echo (Cela peut prendre 2-5 minutes)
echo.

py -m pip install --upgrade pip >nul 2>&1
py -m pip install -r requirements.txt

if errorlevel 1 (
    echo ERREUR : Impossible d'installer les dependances
    echo.
    echo Verifiez votre connexion Internet
    pause
    exit /b 1
)

echo.
echo ========================================
echo    INSTALLATION REUSSIE !
echo ========================================
echo.
echo Vous pouvez maintenant utiliser l'application !
echo.
echo Pour lancer l'app :
echo    Double-cliquez sur : LANCER_APP.bat
echo.
pause
