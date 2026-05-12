param()
$lines = Get-Content 'src/main/java/com/wangver/hanime/service/DownloadService.java'
$out = for ($i = 358; $i -le 465 -and $i -lt $lines.Count; $i++) {
    '{0}: {1}' -f ($i+1), $lines[$i]
}
$out | Out-File 'process_section.txt' -Encoding UTF8
