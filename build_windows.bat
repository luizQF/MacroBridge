@echo off
echo ============================================
echo   Build Macro IA para Windows
echo ============================================
echo.

:: Verifica se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale o Python 3.8+ do python.org
    pause
    exit /b 1
)

echo [1/4] Python detectado!
echo.

:: Cria ambiente virtual (opcional, mas recomendado)
if not exist "venv" (
    echo [2/4] Criando ambiente virtual...
    python -m venv venv
) else (
    echo [2/4] Ambiente virtual ja existe.
)

:: Ativa ambiente virtual
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

:: Instala dependencias
echo.
echo [3/4] Instalando dependencias...
pip install -r requirements.txt --quiet

:: Build com PyInstaller
echo.
echo [4/4] Criando executavel...
pyinstaller --onefile --windowed --name="MacroIA_Universal" --icon=NONE --add-data "dataset;dataset" --clean Macro.py

echo.
echo ============================================
echo   BUILD CONCLUIDO!
echo ============================================
echo.
echo O executavel esta em: dist\MacroIA_Universal.exe
echo.
echo Para distribuir, copie tambem a pasta 'dataset' junto com o .exe
echo.
pause