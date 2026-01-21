#!/bin/bash
# run_frontend.sh - Rodar frontend sem ativar venv

cd "$(dirname "$0")"
./venv/Scripts/streamlit.exe run frontend/app.py
