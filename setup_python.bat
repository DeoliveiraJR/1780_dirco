@echo off
REM Adicionar Python ao PATH do Windows
setx PATH "%PATH%;C:\Users\morai\AppData\Local\Programs\Python\Python314;C:\Users\morai\AppData\Local\Programs\Python\Python314\Scripts"

echo.
echo ========================================
echo Python foi adicionado ao PATH!
echo ========================================
echo.
echo IMPORTANTE: Feche TODOS os terminais abertos
echo e abra um NOVO terminal (PowerShell ou CMD)
echo para as mudancas entrarem em efeito.
echo.
echo Depois execute: python --version
echo.
pause
