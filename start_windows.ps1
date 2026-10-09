[CmdletBinding()]
param([ValidateSet("demo", "local")][string]$Profile = "demo", [switch]$Reload)
$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
Set-Location $PSScriptRoot
$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Run .\setup_windows.ps1 first." }
$Arguments = @("scripts/dev.py", "serve", "--profile", $Profile)
if ($Reload) { $Arguments += "--reload" }
& $Python @Arguments
exit $LASTEXITCODE
