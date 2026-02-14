@echo off
chcp 65001 >nul
cls

echo.
echo ╔════════════════════════════════════════╗
echo ║   🎥  VIDEO DOWNLOADER                 ║
echo ║   INSTALLATION (À exécuter qu'une fois)║
echo ╚════════════════════════════════════════╝
echo.

REM Vérifier Python
py --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERREUR : Python n'est pas installé !
    echo.
    echo 📥 Étapes :
    echo  1. Aller sur https://python.org/downloads/
    echo  2. Télécharger Python 3.10 ou plus récent
    echo  3. COCHER "Add Python to PATH" lors de l'installation
    echo  4. Relancer ce fichier après
    echo.
    pause
    exit /b 1
)

echo ✅ Python trouvé
echo.

REM Créer venv (une seule fois)
if exist "venv\" (
    echo ✅ Environnement virtuel déjà créé
    echo.
) else (
    echo 📦 Création de l'environnement virtuel...
    py -m venv venv
    if errorlevel 1 (
        echo ❌ ERREUR : Impossible de créer venv
        pause
        exit /b 1
    )
    echo ✅ Environnement virtuel créé
    echo.
)

REM Activer et installer les dépendances
call venv\Scripts\activate.bat

echo 📚 Installation des dépendances...
echo    (Cela peut prendre 2-5 minutes)
echo.

pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ ERREUR : Impossible d'installer les dépendances
    echo.
    echo Vérifiez votre connexion Internet
    pause
    exit /b 1
)

echo.
echo ✅✅✅ INSTALLATION RÉUSSIE ! ✅✅✅
echo.
echo 🎉 Vous pouvez maintenant utiliser l'application !
echo.
echo 📝 À présent, pour lancer l'app :
echo    Double-cliquez sur : LANCER_APP.bat
echo.
pause
