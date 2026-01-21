#!/bin/bash
# run_backend.sh - Rodar backend sem ativar venv

cd "$(dirname "$0")"
./venv/Scripts/python.exe backend/run.py
