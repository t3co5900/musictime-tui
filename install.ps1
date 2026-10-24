# Instala musictime en Windows (PowerShell). Para actualizar: git pull; .\install.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$venv = Join-Path $env:LOCALAPPDATA "musictime\venv"
python -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
& "$venv\Scripts\python.exe" -m pip install --quiet -e .

# Comando `musictime` disponible desde cualquier terminal
$bin = Join-Path $env:LOCALAPPDATA "musictime\bin"
New-Item -ItemType Directory -Force $bin | Out-Null
Set-Content -Path (Join-Path $bin "musictime.cmd") -Value "@echo off`r`n`"$venv\Scripts\musictime.exe`" %*"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$bin*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$bin", "User")
    Write-Host "Se agregó $bin al PATH: abrí una terminal nueva."
}

$cfgDir = Join-Path $env:USERPROFILE ".config\musictime"
New-Item -ItemType Directory -Force $cfgDir | Out-Null
$cfg = Join-Path $cfgDir "config.json"
if (-not (Test-Path $cfg)) {
    Set-Content -Path $cfg -Value '{"client_id": "PEGA_AQUI_TU_CLIENT_ID"}'
    Write-Host "Editá $cfg con tu Client ID de Spotify."
}
Write-Host "Listo. Primera vez: musictime login. Después: musictime"
