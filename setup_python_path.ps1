# Script para adicionar Python ao PATH
$pythonPath = "C:\Users\morai\AppData\Local\Programs\Python\Python314"
$pythonScripts = "$pythonPath\Scripts"
$currentPath = [Environment]::GetEnvironmentVariable('PATH', 'User')

if ($currentPath -notlike "*$pythonPath*") {
    $newPath = $currentPath + ";$pythonPath;$pythonScripts"
    [Environment]::SetEnvironmentVariable('PATH', $newPath, 'User')
    Write-Host "✓ Python adicionado ao PATH com sucesso!" -ForegroundColor Green
    Write-Host "Você precisa FECHAR e ABRIR um novo terminal para as mudanças entrarem em efeito." -ForegroundColor Yellow
} else {
    Write-Host "✓ Python já está no PATH" -ForegroundColor Green
}

# Testar Python
Write-Host "`nTestando Python..." -ForegroundColor Cyan
& "$pythonPath\python.exe" --version
