@echo off
cls

echo.
echo ========================================
echo    VIDEO DOWNLOADER
echo    Demarrage...
echo ========================================
echo.

REM Verifier que venv existe
if not exist "venv\" (
    echo ERREUR : L'installation n'a pas ete faite !
    echo.
    echo Veuillez d'abord executer :
    echo    INSTALLER.bat
    echo.
    pause
    exit /b 1
)

REM Activer venv
call venv\Scripts\activate.bat

REM Lancer l'app
echo OK - Demarrage de Video Downloader...
echo.
echo L'application s'ouvre dans votre navigateur
echo.
echo Pour arreter l'application, appuyez sur CTRL + C
echo ========================================
echo.

streamlit run app.py

pause
