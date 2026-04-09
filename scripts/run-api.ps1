param(
    [int]$PreferredPort = 8010,
    [int]$MaxPortChecks = 20,
    [switch]$NoReload
)

$ErrorActionPreference = "Stop"
$pythonExe = ".\.venv\Scripts\python.exe"
$hostAddress = "127.0.0.1"

function Test-PortAvailable {
    param(
        [string]$HostAddress,
        [int]$Port
    )

    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse($HostAddress), $Port)
        $listener.Start()
        return $true
    } catch {
        return $false
    } finally {
        if ($listener -ne $null) {
            $listener.Stop()
        }
    }
}

function Get-PortOwnerDescription {
    param([int]$Port)

    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $connection) {
        return $null
    }

    $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
    if ($process) {
        return "$($process.ProcessName) (PID $($process.Id))"
    }

    return "PID $($connection.OwningProcess)"
}

if (-not (Test-Path $pythonExe)) {
    throw "Venv introuvable. Lancez d'abord .\\scripts\\setup-venv.ps1"
}

$selectedPort = $PreferredPort
$attempt = 0

while (-not (Test-PortAvailable -HostAddress $hostAddress -Port $selectedPort)) {
    $owner = Get-PortOwnerDescription -Port $selectedPort
    if ($owner) {
        Write-Host "Le port $selectedPort est déjà utilisé par $owner." -ForegroundColor Yellow
    } else {
        Write-Host "Le port $selectedPort n'est pas disponible." -ForegroundColor Yellow
    }

    $attempt += 1
    if ($attempt -ge $MaxPortChecks) {
        throw "Aucun port libre trouvé entre $PreferredPort et $selectedPort."
    }

    $selectedPort += 1
}

if ($selectedPort -ne $PreferredPort) {
    Write-Host "Bascule automatique sur le port $selectedPort." -ForegroundColor Cyan
}

$uvicornArgs = @(
    "-m",
    "uvicorn",
    "maintenance_preventive.api.main:app",
    "--host",
    $hostAddress,
    "--port",
    $selectedPort.ToString()
)

if (-not $NoReload) {
    $uvicornArgs += "--reload"
}

Write-Host "API disponible sur http://${hostAddress}:$selectedPort/docs" -ForegroundColor Green
& $pythonExe @uvicornArgs
