#!/bin/bash
# Script para restaurar Git Bash

# Limpar PATH e restaurar valores corretos
export PATH="/mingw64/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/c/Program Files/Git/cmd:/c/Windows/system32:/c/Windows:/c/Users/morai/AppData/Local/Programs/Python/Python314:/c/Users/morai/AppData/Local/Programs/Python/Python314/Scripts"

echo "PATH restaurado!"
echo "Testando ls..."
ls -la
