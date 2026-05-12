@echo off
set JAVA_HOME=D:\MyDocument\depend\Java21
cd /d D:\Ubuntu-Share\Hanime1-Vedio-Download
"%JAVA_HOME%\bin\jdeps" --ignore-missing-deps --print-module-deps --multi-release 21 target/hanime-downloader-web-1.0.0-SNAPSHOT.jar > target/jdeps_out.txt 2>&1
echo JDEPSEXIT=%ERRORLEVEL%
