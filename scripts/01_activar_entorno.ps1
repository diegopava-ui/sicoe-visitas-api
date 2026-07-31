# ============================================
# SICOE FRAMEWORK
# Activación del entorno de desarrollo
# ============================================

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " SICOE FRAMEWORK - ACTIVANDO ENTORNO " -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "C:\SICOE\sicoe_visitas_api"

if (!(Test-Path ".\.venv")) {

    Write-Host "ERROR: No existe el entorno virtual." -ForegroundColor Red
    exit

}

& ".\.venv\Scripts\Activate.ps1"

$env:WEASYPRINT_DLL_DIRECTORIES="C:\msys64\ucrt64\bin"

Write-Host ""
Write-Host "Entorno virtual........ OK" -ForegroundColor Green
Write-Host "WeasyPrint............. OK" -ForegroundColor Green
Write-Host ""