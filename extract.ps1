$l = Get-Content "src/main/java/com/wangver/hanime/service/DownloadService.java"
$o = $l[363..410] -join "`r`n"
Write-Host $o
