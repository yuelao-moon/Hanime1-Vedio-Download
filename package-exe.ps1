param(
    [switch]$NoBuild,
    [switch]$Portable
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

# Set Java environment
$env:JAVA_HOME = "D:\MyDocument\depend\Java21"
$env:Path = "$env:JAVA_HOME\bin;D:\MyDocument\depend\apache-maven-3.6.3-bin\apache-maven-3.6.3\bin;$env:Path"

# ========== 1. Build JAR ==========
if (-not $NoBuild) {
    Write-Host "=== [1/6] Building JAR ===" -ForegroundColor Cyan
    mvn clean package -DskipTests -q
    if ($LASTEXITCODE -ne 0) { throw "Maven build failed" }
}

# ========== 2. Find JAR ==========
Write-Host "=== [2/6] Locating JAR ===" -ForegroundColor Cyan
$jarPath = Get-ChildItem -Path "$ProjectRoot\target\*.jar" | Where-Object { $_.Name -notlike "*.jar.original" } | Select-Object -First 1
if (-not $jarPath) { throw "No JAR found in target/" }
Write-Host "JAR: $($jarPath.Name)" -ForegroundColor Cyan

$javaHome = $env:JAVA_HOME

# ========== 3. Analyze module dependencies ==========
Write-Host "=== [3/6] Analyzing module dependencies ===" -ForegroundColor Cyan
$modulesFile = "$ProjectRoot\target\modules.txt"
if (Test-Path $modulesFile) { Remove-Item $modulesFile -Force }

$modules = "ALL-MODULE-PATH"  # 兜底
$jdepsFound = $false
if (Test-Path "$javaHome\bin\jdeps.exe") {
    & "$javaHome\bin\jdeps.exe" --ignore-missing-deps --print-module-deps --multi-release 21 $jarPath.FullName 2>$null | Out-File $modulesFile -Encoding UTF8
    $modules = (Get-Content $modulesFile -Raw -ErrorAction SilentlyContinue).Trim()
    if (-not [string]::IsNullOrEmpty($modules)) { $jdepsFound = $true }
}
if (-not $jdepsFound) {
    Write-Host "jdeps unavailable; using common module set" -ForegroundColor Yellow
    $modules = "java.base,java.logging,java.xml,java.naming,java.sql,java.management,java.instrument,java.net.http,jdk.unsupported,java.desktop,java.scripting,java.compiler,jdk.zipfs"
}
Write-Host "Required modules: $modules" -ForegroundColor Cyan

# ========== 4. Create minimal JRE with jlink ==========
Write-Host "=== [4/6] Creating minimal JRE (jlink) ===" -ForegroundColor Cyan
$runtimeDir = "$ProjectRoot\target\runtime"
if (Test-Path $runtimeDir) { Remove-Item -Path $runtimeDir -Recurse -Force }

$jlinkArgs = @(
    "--module-path", "$javaHome\jmods"
    "--add-modules", $modules
    "--output", $runtimeDir
    "--strip-debug"
    "--no-header-files"
    "--no-man-pages"
)

$oldPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& "$javaHome\bin\jlink.exe" $jlinkArgs 2>&1
$ErrorActionPreference = $oldPreference
if ($LASTEXITCODE -ne 0) {
    Write-Host "jlink with specific modules failed; retrying with broader module set" -ForegroundColor Yellow
    Remove-Item -Path $runtimeDir -Recurse -Force -ErrorAction SilentlyContinue
    $broaderModules = "java.base,java.logging,java.xml,java.naming,java.sql,java.management,java.instrument,java.net.http,jdk.unsupported,java.desktop,java.scripting,java.compiler,jdk.zipfs,java.security.jgss,java.security.sasl,java.transaction.xa,jdk.crypto.cryptoki,jdk.crypto.ec,jdk.localedata"
    $jlinkArgs[3] = $broaderModules
    $ErrorActionPreference = "Continue"
    & "$javaHome\bin\jlink.exe" $jlinkArgs 2>&1
    $ErrorActionPreference = $oldPreference
    if ($LASTEXITCODE -ne 0) { throw "jlink failed. Ensure JDK 21+ with jmods available." }
}

$runtimeSize = (Get-ChildItem -Path $runtimeDir -Recurse | Measure-Object -Property Length -Sum).Sum
Write-Host "Runtime size: $([math]::Round($runtimeSize/1MB, 1)) MB" -ForegroundColor Cyan

# ========== 5. Prepare staging ==========
Write-Host "=== [5/6] Preparing staging ===" -ForegroundColor Cyan
$stageDir = "$ProjectRoot\target\staging"
if (Test-Path $stageDir) { Remove-Item -Path $stageDir -Recurse -Force }
New-Item -ItemType Directory -Path $stageDir -Force | Out-Null
Copy-Item $jarPath.FullName -Destination "$stageDir\$($jarPath.Name)" -Force

# Copy extra files needed at runtime (Playwright browsers, config defaults)
if (Test-Path "$ProjectRoot\cache") {
    Copy-Item -Path "$ProjectRoot\cache" -Destination "$stageDir\cache" -Recurse -ErrorAction SilentlyContinue
}

# ========== 6. Package EXE with jpackage ==========
Write-Host "=== [6/6] Packaging EXE (jpackage) ===" -ForegroundColor Cyan
$outputDir = "$ProjectRoot\dist"
if (Test-Path $outputDir) { Remove-Item -Path $outputDir -Recurse -Force }
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

if ($Portable) {
    # ---- Portable mode: app-image (directory, no installer) ----
    $appName = "HanimeMediaCenter"
    $appDir = "$outputDir\$appName"
    & "$javaHome\bin\jpackage.exe" `
        --input $stageDir `
        --main-jar $jarPath.Name `
        --runtime-image $runtimeDir `
        --main-class org.springframework.boot.loader.launch.JarLauncher `
        --name $appName `
        --type "app-image" `
        --app-version "1.0.0" `
        --java-options "-Xmx512m" `
        --java-options "-Djava.awt.headless=true" `
        --dest $outputDir `
        --vendor "HanimeMediaCenter" `
        --verbose 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "=== SUCCESS (Portable) ===" -ForegroundColor Green
        Write-Host "Portable app directory: $appDir" -ForegroundColor Green
        $appSize = (Get-ChildItem -Path $appDir -Recurse | Measure-Object -Property Length -Sum).Sum
        Write-Host "Total size: $([math]::Round($appSize/1MB, 1)) MB" -ForegroundColor Green
        Write-Host "Run: $appDir\$appName.exe" -ForegroundColor Green

        # Create a portable batch launcher as fallback
        $launcherPath = "$outputDir\HanimeMediaCenter-Portable.bat"
        @"
@echo off
setlocal
set "APP_DIR=%~dp0%appName%"
start "" "%APP_DIR%\%appName%.exe"
exit /b
"@ -replace "%appName%", $appName | Out-File -FilePath $launcherPath -Encoding ASCII
    }

} else {
    # ---- Installer mode: single EXE installer with bundled JRE ----
    & "$javaHome\bin\jpackage.exe" `
        --input $stageDir `
        --main-jar $jarPath.Name `
        --runtime-image $runtimeDir `
        --main-class org.springframework.boot.loader.launch.JarLauncher `
        --name "HanimeMediaCenter" `
        --type "exe" `
        --app-version "1.0.0" `
        --java-options "-Xmx512m" `
        --java-options "-Djava.awt.headless=true" `
        --dest $outputDir `
        --vendor "HanimeMediaCenter" `
        --win-console `
        --win-dir-chooser `
        --win-menu `
        --win-shortcut `
        --win-per-user-install `
        --verbose 2>&1

    if ($LASTEXITCODE -eq 0) {
        $installer = Get-ChildItem -Path $outputDir -Filter "*.exe" | Select-Object -First 1
        Write-Host "=== SUCCESS ===" -ForegroundColor Green
        Write-Host "Installer: $($installer.FullName)" -ForegroundColor Green
        Write-Host "Size: $([math]::Round($installer.Length/1MB, 1)) MB" -ForegroundColor Green
    } else {
        Write-Host "=== FAILED ===" -ForegroundColor Red
        Write-Host "Check jpackage logs at %LOCALAPPDATA%\jpackage.log" -ForegroundColor Yellow
        exit 1
    }
}
