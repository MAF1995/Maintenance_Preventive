$ErrorActionPreference = "Stop"
$pythonExe = ".\.venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "Venv introuvable. Lancez d'abord .\\scripts\\setup-venv.ps1"
}

& $pythonExe -m maintenance_preventive.features.engineering

