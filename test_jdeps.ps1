$ErrorActionPreference = "Continue"
$env:JAVA_HOME = "D:\MyDocument\depend\Java21"
$env:Path = "$env:JAVA_HOME\bin;$env:Path"

$out = & "$env:JAVA_HOME\bin\jdeps.exe" --ignore-missing-deps --print-module-deps --multi-release 21 "target/hanime-downloader-web-1.0.0-SNAPSHOT.jar" 2>&1
$out | Out-File "target/jdeps_output.txt" -Encoding UTF8
Write-Host "jdeps output: $out"
Write-Host "DONE"