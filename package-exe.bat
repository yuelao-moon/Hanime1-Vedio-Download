@echo off
set JAVA_HOME=D:\MyDocument\depend\Java21
set PATH=%JAVA_HOME%\bin;D:\MyDocument\depend\apache-maven-3.6.3-bin\apache-maven-3.6.3\bin;%PATH%
cd /d D:\Ubuntu-Share\Hanime1-Vedio-Download

echo === [1/6] Building JAR ===
mvn clean package -DskipTests -q
if %ERRORLEVEL% neq 0 (echo MAVEN FAILED & exit /b 1)

echo === [2/6] Locating JAR ===
set JAR_FILE=target\hanime-downloader-web-1.0.0-SNAPSHOT.jar
if not exist "%JAR_FILE%" (echo JAR NOT FOUND & exit /b 1)
echo JAR: %JAR_FILE%

echo === [3/6] Analyzing module dependencies ===
"%JAVA_HOME%\bin\jdeps" --ignore-missing-deps --print-module-deps --multi-release 21 "%JAR_FILE%" 2>nul > target\modules.txt
set /p JDEP_MODULES=<target\modules.txt
if "%JDEP_MODULES%"=="" (
    echo jdeps unavailable, using default module set
    set JDEP_MODULES=java.base,java.logging,java.xml,java.naming,java.sql,java.management,java.instrument,java.net.http,jdk.unsupported,java.desktop,java.scripting,java.compiler,jdk.zipfs
)
echo Required modules: %JDEP_MODULES%

echo === [4/6] Creating minimal JRE (jlink) ===
if exist target\runtime rmdir /s /q target\runtime
"%JAVA_HOME%\bin\jlink" --module-path "%JAVA_HOME%\jmods" --add-modules %JDEP_MODULES% --output target\runtime --strip-debug --no-header-files --no-man-pages
if %ERRORLEVEL% neq 0 (
    echo jlink failed with specific modules, retrying with broader set
    if exist target\runtime rmdir /s /q target\runtime
    "%JAVA_HOME%\bin\jlink" --module-path "%JAVA_HOME%\jmods" --add-modules java.base,java.logging,java.xml,java.naming,java.sql,java.management,java.instrument,java.net.http,jdk.unsupported,java.desktop,java.scripting,java.compiler,jdk.zipfs,java.security.jgss,java.security.sasl,java.transaction.xa,jdk.crypto.cryptoki,jdk.crypto.ec,jdk.localedata --output target\runtime --strip-debug --no-header-files --no-man-pages
    if %ERRORLEVEL% neq 0 (echo JLINK FAILED & exit /b 1)
)

echo === [5/6] Preparing staging ===
if exist target\staging rmdir /s /q target\staging
mkdir target\staging
copy "%JAR_FILE%" target\staging\ >nul

echo === [6/6] Packaging EXE (jpackage) ===
if exist dist rmdir /s /q dist
mkdir dist

"%JAVA_HOME%\bin\jpackage" ^
    --input target\staging ^
    --main-jar hanime-downloader-web-1.0.0-SNAPSHOT.jar ^
    --runtime-image target\runtime ^
    --main-class org.springframework.boot.loader.launch.JarLauncher ^
    --name "HanimeMediaCenter" ^
    --type "exe" ^
    --app-version "1.0.0" ^
    --java-options "-Xmx512m" ^
    --java-options "-Djava.awt.headless=true" ^
    --dest dist ^
    --vendor "HanimeMediaCenter" ^
    --win-console ^
    --win-dir-chooser ^
    --win-menu ^
    --win-shortcut ^
    --win-per-user-install ^
    --verbose 2>&1

if %ERRORLEVEL% equ 0 (
    echo === SUCCESS ===
    dir dist\*.exe
) else (
    echo === FAILED ===
    echo Check %%LOCALAPPDATA%%\jpackage.log for details
    exit /b 1
)
