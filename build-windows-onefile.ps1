param(
    [switch]$Clean,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Assert-Command {
    param(
        [string]$Name,
        [string]$InstallHint
    )
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name 未找到。$InstallHint"
    }
}

Assert-Command "python" "Install Python 3.11+ and add it to PATH."

if ($Clean) {
    Write-Step "Clean old build outputs"
    Remove-Item -LiteralPath "$Root\build" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath "$Root\dist" -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Step "Install and verify dependencies"
python -m pip install --upgrade pip
python -m pip install -r "$Root\python_backend\requirements.txt"
python -m pip install "pyinstaller>=6.0,<7"

Write-Step "Python compile check"
python -m compileall -q "$Root\python_backend"

if (Get-Command "node" -ErrorAction SilentlyContinue) {
    Write-Step "Frontend JavaScript syntax check"
    node --check "$Root\src\main\resources\static\app.js"
} else {
    Write-Host "node was not found; skipping frontend JavaScript syntax check." -ForegroundColor Yellow
}

if (-not $SkipTests) {
    Write-Step "Run automated tests"
    python -m pytest "$Root\python_backend\tests" -v
}

Write-Step "Build one-file executable with PyInstaller"
python -m PyInstaller --clean --noconfirm "$Root\HanimeMediaCenter.spec"

$ExePath = Join-Path $Root "dist\HanimeMediaCenter.exe"
if (-not (Test-Path -LiteralPath $ExePath)) {
    throw "Build failed; missing $ExePath"
}

Write-Step "Build completed"
Write-Host $ExePath -ForegroundColor Green
