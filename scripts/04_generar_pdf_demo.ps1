# ============================================
# SICOE VISITAS
# Generación local del PDF de demostración
# ============================================

Set-Location "C:\SICOE\sicoe_visitas_api"

if (!(Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "ERROR: No existe el entorno virtual." -ForegroundColor Red
    exit 1
}

$env:WEASYPRINT_DLL_DIRECTORIES = "C:\msys64\ucrt64\bin"

Write-Host ""
Write-Host "Generando informe de visita..." -ForegroundColor Cyan

& ".\.venv\Scripts\python.exe" `
    ".\scripts\generar_pdf_demo.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: No se pudo generar el PDF." -ForegroundColor Red
    exit $LASTEXITCODE
}

$pdf = "C:\SICOE\sicoe_visitas_api\output\Informe_Visita_6.pdf"

if (Test-Path $pdf) {
    Write-Host "PDF generado correctamente." -ForegroundColor Green
    Write-Host $pdf -ForegroundColor Yellow
    Start-Process $pdf
}