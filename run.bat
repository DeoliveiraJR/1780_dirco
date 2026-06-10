@echo off
REM Script para inicializar o Streamlit com o interpretador correto (venv)
REM Este script garante que o app sempre rode com o Python do ambiente virtual

cd /d "%~dp0"

echo Iniciando UAN Dashboard com o ambiente virtual correto...
echo.

REM Executa com caminho absoluto do Python da venv
"%~dp0.venv\Scripts\python.exe" -m streamlit run frontend/app.py

REM Se houver erro de saída, pausa para o usuário ver a mensagem
if errorlevel 1 (
    echo.
    echo Erro ao iniciar o app. Verificar logs acima.
    pause
)
