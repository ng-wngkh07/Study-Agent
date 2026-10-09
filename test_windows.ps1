[CmdletBinding()]
param()
$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
Set-Location $PSScriptRoot
$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Run .\setup_windows.ps1 first." }
& $Python -m pytest -c pytest.windows.ini
exit $LASTEXITCODE
