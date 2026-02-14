@echo off
chcp 65001 >nul
cls

echo.
echo ╔════════════════════════════════════════╗
echo ║   🎥  VIDEO DOWNLOADER                 ║
echo ║   Démarrage...                         ║
echo ╚════════════════════════════════════════╝
echo.

REM Vérifier que venv existe
if not exist "venv\" (
    echo ❌ ERREUR : L'installation n'a pas été faite !
    echo.
    echo 📝 Veuillez d'abord exécuter :
    echo    → INSTALLER.bat
    echo.
    pause
    exit /b 1
)

REM Activer venv
call venv\Scripts\activate.bat

REM Lancer l'app
echo ✅ Démarrage de Video Downloader...
echo.
echo 🌐 L'application s'ouvre dans votre navigateur
echo.
echo Pour arrêter l'application, appuyez sur CTRL + C
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

streamlit run app.py

pause
