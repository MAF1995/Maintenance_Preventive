param(
    [int]$Port = 5000
)

$ErrorActionPreference = "Stop"
$pythonExe = ".\.venv\Scripts\python.exe"
$projectRoot = (Resolve-Path ".").Path
$mlflowDbPath = Join-Path $projectRoot "artifacts\mlflow\mlflow.db"
$mlflowArtifactsPath = Join-Path $projectRoot "artifacts\mlflow\artifacts"

if (-not (Test-Path $pythonExe)) {
    throw "Venv introuvable. Lancez d'abord .\\scripts\\setup-venv.ps1"
}

New-Item -ItemType Directory -Force -Path (Split-Path $mlflowDbPath -Parent) | Out-Null
New-Item -ItemType Directory -Force -Path $mlflowArtifactsPath | Out-Null

$backendStoreUri = "sqlite:///{0}" -f ($mlflowDbPath -replace "\\", "/")
$artifactRootUri = "file:///{0}" -f ($mlflowArtifactsPath -replace "\\", "/")

Write-Host "MLflow UI disponible sur http://127.0.0.1:$Port" -ForegroundColor Green
& $pythonExe -m mlflow server `
    --host 127.0.0.1 `
    --port $Port `
    --backend-store-uri $backendStoreUri `
    --default-artifact-root $artifactRootUri `
    --no-serve-artifacts
