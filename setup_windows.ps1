# Full setup; -DemoOnly avoids Ollama and model downloads.
[CmdletBinding()]
param([switch]$DemoOnly)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
if ($env:OS -ne 'Windows_NT') { throw 'This installer is for Windows only.' }
Set-Location $PSScriptRoot
. (Join-Path $PSScriptRoot 'scripts\windows_setup.ps1')
$manifest = Get-Content 'requirements-windows-tools.json' -Raw | ConvertFrom-Json
$profile = if ($DemoOnly) { 'demo' } else { 'full' }
$tools = @{}
foreach ($package in $manifest.packages) {
    if ($package.profiles -contains $profile) {
        Write-Host "Checking $($package.name)..."
        $tools[$package.name] = Ensure-WindowsTool $package
    }
}
$Python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) {
    Invoke-NativeChecked -File $tools['python'] -Arguments @('-m', 'venv', '.venv')
}
$version = & $Python -c "import sys; print('%s.%s' % sys.version_info[:2])"
if ($LASTEXITCODE -ne 0 -or $version -ne $manifest.python_minor) {
    throw 'Existing .venv is not Python 3.12. Rename it to .venv-backup and rerun setup.'
}
Invoke-NativeChecked -File $Python -Arguments @('-m', 'pip', 'install', '-r', 'requirements-windows.txt')
Invoke-NativeChecked -File $Python -Arguments @('-m', 'pip', 'check')
if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env' }
Invoke-NativeChecked -File $Python -Arguments @('scripts/dev.py', 'demo')
if (-not $DemoOnly) {
    # Preserve customized endpoints/models; automatic setup uses the manifest only.
    $defaults = @{ OLLAMA_BASE_URL = @('http://localhost:11434', 'http://127.0.0.1:11434');
        DEFAULT_CHAT_MODEL = @($manifest.models[0].name); DEFAULT_EMBED_MODEL = @($manifest.models[1].name);
        OLLAMA_AUX_CHAT_MODEL = @($manifest.models[2].name) }
    foreach ($line in Get-Content '.env') {
        if ($line -match '^\s*(OLLAMA_BASE_URL|DEFAULT_CHAT_MODEL|DEFAULT_EMBED_MODEL|OLLAMA_AUX_CHAT_MODEL)\s*=\s*(.+?)\s*$') {
            $key = $Matches[1]; $value = $Matches[2].Trim([char[]]@('"', "'"))
            if ($defaults[$key] -notcontains $value) { throw 'Custom .env: use -DemoOnly or coordinate the install plan; existing settings were preserved.' }
        }
    }
    Ensure-OllamaReady -File $tools['ollama'] -BaseUrl $manifest.ollama_base_url
    foreach ($model in $manifest.models) {
        Write-Host "Preparing $($model.role): $($model.name)..."
        Invoke-NativeChecked -File $tools['ollama'] -Arguments @('pull', $model.name)
    }
    $tags = Invoke-RestMethod "$($manifest.ollama_base_url)/api/tags" -TimeoutSec 10
    foreach ($model in $manifest.models) {
        if (-not (Test-OllamaModelInstalled -Name $model.name -Installed $tags.models.name)) { throw "Missing model after pull: $($model.name)" }
    }
    Invoke-NativeChecked -File $Python -Arguments @('scripts/dev.py', 'check', '--require-model')
} else {
    Invoke-NativeChecked -File $Python -Arguments @('scripts/dev.py', 'check')
}
Write-Host 'Setup complete. Run .\start_windows.ps1, then open http://127.0.0.1:8000.'
