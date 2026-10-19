$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    python -m venv (Join-Path $ProjectRoot ".venv")
}
& $Python -m pip install -e ".[dev]"
Write-Host "Demo environment ready; no model weights were downloaded."
