$ErrorActionPreference = "Stop"

$Proyecto = "C:\SICOE\sicoe_visitas_api"
$Python = Join-Path $Proyecto ".venv\Scripts\python.exe"
$Puerto = 8000

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "       SICOE VISITAS - BACKEND" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

if (-not (Test-Path $Proyecto)) {
    Write-Host "No existe la carpeta del backend:" -ForegroundColor Red
    Write-Host $Proyecto -ForegroundColor Red
    Read-Host "Presiona Enter para cerrar"
    exit 1
}

if (-not (Test-Path $Python)) {
    Write-Host "No se encontró el Python del entorno virtual:" -ForegroundColor Red
    Write-Host $Python -ForegroundColor Red
    Read-Host "Presiona Enter para cerrar"
    exit 1
}

$PuertoOcupado = Get-NetTCPConnection `
    -LocalPort $Puerto `
    -State Listen `
    -ErrorAction SilentlyContinue

if ($PuertoOcupado) {
    Write-Host "El puerto $Puerto ya está ocupado." -ForegroundColor Yellow
    Write-Host "Probablemente FastAPI ya está funcionando." -ForegroundColor Yellow
    Write-Host "Abre: http://127.0.0.1:$Puerto/health" -ForegroundColor Green
    Read-Host "Presiona Enter para cerrar"
    exit 0
}

Set-Location $Proyecto

Write-Host "Iniciando FastAPI en http://127.0.0.1:$Puerto" -ForegroundColor Green
Write-Host "No cierres esta ventana mientras estés trabajando." -ForegroundColor Yellow
Write-Host ""

& $Python -m uvicorn app.main:app `
    --reload `
    --host 127.0.0.1 `
    --port $Puerto

Write-Host ""
Write-Host "El servidor backend se detuvo." -ForegroundColor Yellow
Read-Host "Presiona Enter para cerrar"