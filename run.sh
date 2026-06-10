#!/bin/bash
# Script para inicializar o Streamlit com o interpretador correto (venv)
# Este script garante que o app sempre rode com o Python do ambiente virtual

cd "$(dirname "$0")"

echo "Iniciando UAN Dashboard com o ambiente virtual correto..."
echo ""

# Executa com caminho absoluto do Python da venv
./.venv/Scripts/python.exe -m streamlit run frontend/app.py
