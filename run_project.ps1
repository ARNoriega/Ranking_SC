$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $python) {
    throw "No se encontro Python en PATH."
}

Write-Host "Compilando el proyecto..." -ForegroundColor Cyan
& $python.Source -m compileall -q application database processing simulation tests ranking.py "simulación.py"
if ($LASTEXITCODE -ne 0) {
    throw "La compilacion fallo."
}

Write-Host "Compilacion correcta." -ForegroundColor Green
Write-Host "Iniciando la aplicacion visual..." -ForegroundColor Cyan
& $python.Source -m application.visual
if ($LASTEXITCODE -ne 0) {
    throw "La aplicacion termino con errores."
}
