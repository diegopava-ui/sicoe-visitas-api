param(
    [switch]$NoFrontend,
    [switch]$NoBackend,
    [switch]$NoDocker,
    [switch]$SkipAlembicCheck
)

$ErrorActionPreference = "Stop"

$BackendPath = "C:\SICOE\sicoe_visitas_api"
$FrontendPath = "C:\SICOE\sicoe_visitas_frontend"
$VenvActivate = Join-Path $BackendPath ".venv\Scripts\Activate.ps1"
$WeasyPrintDllPath = "C:\msys64\ucrt64\bin"
$BackendUrl = "http://127.0.0.1:8000"
$FrontendUrl = "http://127.0.0.1:5173"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Stop-WithError {
    param([string]$Message)
    Write-Host ""
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

Write-Step "SICOE VISITAS - VALIDACION DEL ENTORNO"

if (-not (Test-Path $BackendPath)) {
    Stop-WithError "No existe la carpeta del backend: $BackendPath"
}

if (-not $NoFrontend -and -not (Test-Path $FrontendPath)) {
    Stop-WithError "No existe la carpeta del frontend: $FrontendPath"
}

if (-not (Test-Path $VenvActivate)) {
    Stop-WithError "No existe el entorno virtual: $VenvActivate"
}

if (-not (Test-Path $WeasyPrintDllPath)) {
    Stop-WithError "No existe la carpeta de DLL de WeasyPrint: $WeasyPrintDllPath"
}

$env:WEASYPRINT_DLL_DIRECTORIES = $WeasyPrintDllPath
Write-Host "WeasyPrint DLL: OK ($env:WEASYPRINT_DLL_DIRECTORIES)" -ForegroundColor Green

$currentUserValue = [Environment]::GetEnvironmentVariable(
    "WEASYPRINT_DLL_DIRECTORIES",
    "User"
)

if ($currentUserValue -ne $WeasyPrintDllPath) {
    [Environment]::SetEnvironmentVariable(
        "WEASYPRINT_DLL_DIRECTORIES",
        $WeasyPrintDllPath,
        "User"
    )
    Write-Host "Variable permanente de WeasyPrint actualizada." -ForegroundColor Yellow
}

if (-not $NoDocker) {
    Write-Step "VALIDANDO DOCKER DESKTOP"

    $dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $dockerCommand) {
        Write-Host "Docker no está instalado o no está en PATH." -ForegroundColor Yellow
    }
    else {
        docker info *> $null
        if ($LASTEXITCODE -ne 0) {
            $dockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"

            if (Test-Path $dockerDesktop) {
                Write-Host "Docker Desktop está apagado. Iniciándolo..." -ForegroundColor Yellow
                Start-Process $dockerDesktop

                $dockerReady = $false
                for ($i = 1; $i -le 30; $i++) {
                    Start-Sleep -Seconds 2
                    docker info *> $null
                    if ($LASTEXITCODE -eq 0) {
                        $dockerReady = $true
                        break
                    }
                    Write-Host "Esperando Docker... intento $i/30"
                }

                if (-not $dockerReady) {
                    Stop-WithError "Docker no respondió después de 60 segundos."
                }
            }
            else {
                Write-Host "Docker está apagado y no se encontró Docker Desktop.exe." -ForegroundColor Yellow
            }
        }

        if ($LASTEXITCODE -eq 0) {
            Write-Host "Docker: OK" -ForegroundColor Green
        }
    }
}

Write-Step "VALIDANDO POSTGRESQL"

$postgresServices = Get-Service -Name "*postgres*" -ErrorAction SilentlyContinue
if (-not $postgresServices) {
    Stop-WithError "No se encontró ningún servicio PostgreSQL."
}

$runningPostgres = $postgresServices | Where-Object Status -eq "Running"
if (-not $runningPostgres) {
    $serviceToStart = $postgresServices | Select-Object -First 1
    Write-Host "PostgreSQL está detenido. Intentando iniciar $($serviceToStart.Name)..." -ForegroundColor Yellow
    Start-Service $serviceToStart.Name
    Start-Sleep -Seconds 3
}

Get-Service -Name "*postgres*" -ErrorAction SilentlyContinue |
    Format-Table Status, Name, DisplayName -AutoSize

$dbPort = Test-NetConnection localhost -Port 5432 -WarningAction SilentlyContinue
if (-not $dbPort.TcpTestSucceeded) {
    Stop-WithError "PostgreSQL no responde en localhost:5432."
}

Write-Host "PostgreSQL puerto 5432: OK" -ForegroundColor Green

Write-Step "VALIDANDO BACKEND Y ENTORNO VIRTUAL"

Set-Location $BackendPath
. $VenvActivate

if (-not $env:VIRTUAL_ENV) {
    Stop-WithError "El entorno virtual no quedó activo."
}

Write-Host "Entorno virtual activo: $env:VIRTUAL_ENV" -ForegroundColor Green

python -c "import sqlalchemy; import pydantic_settings; import fastapi; import psycopg; print('Dependencias Python: OK')"
if ($LASTEXITCODE -ne 0) {
    Stop-WithError "Falló la validación de dependencias Python."
}

python -c "from weasyprint import HTML; print('WeasyPrint: OK')"
if ($LASTEXITCODE -ne 0) {
    Stop-WithError "WeasyPrint no pudo cargar sus DLL."
}

python -m compileall app
if ($LASTEXITCODE -ne 0) {
    Stop-WithError "El backend contiene errores de compilación."
}

if (-not $SkipAlembicCheck) {
    python -m alembic current
    if ($LASTEXITCODE -ne 0) {
        Stop-WithError "Alembic no pudo consultar la versión actual."
    }
}

$backendPort = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($backendPort) {
    Write-Host "Backend ya está escuchando en el puerto 8000." -ForegroundColor Yellow
}
elseif (-not $NoBackend) {
    Write-Step "INICIANDO BACKEND EN UNA TERMINAL NUEVA"

    $backendCommand = @"
Set-Location '$BackendPath'
`$env:WEASYPRINT_DLL_DIRECTORIES = '$WeasyPrintDllPath'
. '$VenvActivate'
Write-Host 'Backend SICOE VISITAS' -ForegroundColor Cyan
Write-Host 'Swagger: $BackendUrl/docs' -ForegroundColor Green
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"@

    Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "RemoteSigned",
        "-Command", $backendCommand
    )

    Start-Sleep -Seconds 4
}

if (-not $NoFrontend) {
    Write-Step "VALIDANDO E INICIANDO FRONTEND"

    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Stop-WithError "Node.js no está instalado o no está en PATH."
    }

    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        Stop-WithError "npm no está instalado o no está en PATH."
    }

    $frontendPort = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue

    if ($frontendPort) {
        Write-Host "Frontend ya está escuchando en el puerto 5173." -ForegroundColor Yellow
    }
    else {
        $frontendCommand = @"
Set-Location '$FrontendPath'
Write-Host 'Frontend SICOE VISITAS' -ForegroundColor Cyan
npm run dev
"@

        Start-Process powershell.exe -ArgumentList @(
            "-NoExit",
            "-ExecutionPolicy", "RemoteSigned",
            "-Command", $frontendCommand
        )
    }
}

Write-Step "ENTORNO SICOE VISITAS INICIADO"
Write-Host "Backend:  $BackendUrl" -ForegroundColor Green
Write-Host "Swagger:  $BackendUrl/docs" -ForegroundColor Green

if (-not $NoFrontend) {
    Write-Host "Frontend: $FrontendUrl" -ForegroundColor Green
}

Write-Host ""
Write-Host "Cada servicio quedó en su propia terminal." -ForegroundColor Yellow
Write-Host "Para detenerlos, usa Ctrl+C en la terminal correspondiente." -ForegroundColor Yellow
