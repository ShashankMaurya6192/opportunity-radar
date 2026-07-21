param(
    [switch]$Run
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found. Install Python 3.11 or newer first."
}

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt

if (Test-Path "requirements-dev.txt") {
    & $Python -m pip install -r requirements-dev.txt
}

& "$VenvDir\Scripts\alembic.exe" -c alembic.ini upgrade head
& $Python -m pytest -q

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Run the app with:" -ForegroundColor Cyan
Write-Host ".\.venv\Scripts\python.exe -m uvicorn app.main:app --reload"

if ($Run) {
    & $Python -m uvicorn app.main:app --reload
}
