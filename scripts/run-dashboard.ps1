$ErrorActionPreference = "Stop"
$pythonExe = ".\.venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "Venv introuvable. Lancez d'abord .\\scripts\\setup-venv.ps1"
}

$env:MAINTENANCE_API_BASE_URL = "http://127.0.0.1:8011"
& $pythonExe -m streamlit run .\dashboard\streamlit_app.py --server.address 127.0.0.1 --server.port 8501
