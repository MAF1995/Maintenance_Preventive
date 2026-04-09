$ErrorActionPreference = "Stop"
$venvPath = ".\.venv"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"

Write-Host "Préparation du venv local..." -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python n'est pas disponible dans le PATH."
}

if (-not (Test-Path $pythonExe)) {
    Write-Host "Création du venv dans $venvPath" -ForegroundColor Yellow
    python -m venv $venvPath
} else {
    Write-Host "Le venv existe déjà dans $venvPath" -ForegroundColor Green
}

Write-Host "Mise à jour de pip..." -ForegroundColor Cyan
& $pythonExe -m pip install --upgrade pip

Write-Host "Installation des dépendances du projet..." -ForegroundColor Cyan
& $pythonExe -m pip install -r .\requirements.txt

Write-Host ""
Write-Host "Environnement prêt." -ForegroundColor Green
Write-Host "Activation :" -ForegroundColor Cyan
Write-Host ".\.venv\Scripts\Activate.ps1"
