Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$SpecPath = Join-Path $ProjectRoot "packaging\hermes_desktop.spec"

Push-Location $ProjectRoot
try {
    python -m PyInstaller $SpecPath --noconfirm --clean
}
finally {
    Pop-Location
}
