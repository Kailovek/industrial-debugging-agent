param([int]$Port = 8102)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$PidFile = Join-Path $ProjectRoot ".agent-api.pid"
if (-not (Test-Path -LiteralPath $Python)) { throw "Run .\setup.ps1 first." }
if (Test-Path -LiteralPath $PidFile) {
    $ExistingPid = [int](Get-Content -LiteralPath $PidFile -Raw)
    if (Get-Process -Id $ExistingPid -ErrorAction SilentlyContinue) {
        throw "Agent API is already running with PID $ExistingPid."
    }
    Remove-Item -LiteralPath $PidFile -Force
}
$Process = Start-Process -FilePath $Python `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", $Port) `
    -WorkingDirectory $ProjectRoot `
    -RedirectStandardOutput (Join-Path $ProjectRoot "agent-api.log") `
    -RedirectStandardError (Join-Path $ProjectRoot "agent-api-error.log") `
    -WindowStyle Hidden -PassThru
Set-Content -LiteralPath $PidFile -Value $Process.Id -Encoding ascii
Write-Host "Agent API started at http://127.0.0.1:$Port (PID $($Process.Id))."
