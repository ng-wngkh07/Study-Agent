# Offline tests never install software or download models.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\scripts\windows_setup.ps1')
$originalGetTool = (Get-Item Function:Get-ToolPath).ScriptBlock
$script:calls = 0; $script:present = $true
function Get-ToolPath { param($Name); if ($script:present) { return 'fixture-tool.exe' }; return $null }
function Install-WindowsTool { param($Package); $script:calls++; $script:present = $true }
$package = [pscustomobject]@{ name = 'git'; id = 'Git.Git' }
if ((Ensure-WindowsTool $package) -ne 'fixture-tool.exe' -or $script:calls -ne 0) { throw 'Installed tools must be reused.' }
$script:present = $false
if ((Ensure-WindowsTool $package) -ne 'fixture-tool.exe' -or $script:calls -ne 1) { throw 'Missing tool must be installed and resolved again.' }
function Install-WindowsTool { param($Package); throw 'fixture installation failure' }
$script:present = $false
try { Ensure-WindowsTool $package; throw 'Expected installation failure' }
catch { if ($_.Exception.Message -ne 'fixture installation failure') { throw } }
function Install-WindowsTool { param($Package) }
try { Ensure-WindowsTool $package; throw 'Expected unresolved tool failure' }
catch { if ($_.Exception.Message -notlike '*not found after installation*') { throw } }
function FakeNative { $global:LASTEXITCODE = 23 }
try { Invoke-NativeChecked -File 'FakeNative' -Arguments @(); throw 'Expected native failure' }
catch { if ($_.Exception.Message -notlike 'Command failed (23)*') { throw } }
Write-Host 'PASS: reuse, install missing tool, propagate failure, reject unresolved tool, reject native failure.'

if (-not (Test-OllamaModelInstalled 'bge-m3' @('bge-m3:latest'))) { throw 'Default model tag must resolve latest.' }
if (Test-OllamaModelInstalled 'qwen2.5:3b' @('qwen2.5:7b')) { throw 'A different model size must not pass.' }
Write-Host 'PASS: model tag alias and wrong model rejection.'

# An existing launcher without 3.12 must fall back to the actual Python executable.
Set-Item Function:Get-ToolPath $originalGetTool
function Get-Command {
    param($Name, $ErrorAction)
    if ($Name -eq 'py.exe') { return [pscustomobject]@{ Source = 'FakePy' } }
    if ($Name -eq 'python.exe') { return [pscustomobject]@{ Source = 'FakePython' } }
}
function Test-Path { param($Path); return ($Path -eq 'FakePython') }
function FakePy { throw 'No 3.12 registered in launcher' }
function FakePython { $global:LASTEXITCODE = 0; return '3.12' }
if ((Get-ToolPath 'python') -ne 'FakePython') { throw 'Broken launcher blocked Python fallback.' }
Write-Host 'PASS: launcher missing requested Python falls back correctly.'
