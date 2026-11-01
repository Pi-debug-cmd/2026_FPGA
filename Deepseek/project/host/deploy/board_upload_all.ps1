# Upload everything the board run needs, one file at a time (COM8 is exclusive).
#   .\tools\board_upload_all.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root
$files = @(
    @{ Local = 'build\vc_stream_arm';          Remote = '/tmp/vc/vc_stream' },
    @{ Local = 'data\student_v5.blob';         Remote = '/tmp/vc/student_v5.blob' },
    @{ Local = 'data\test_src_32k_s24.raw';    Remote = '/tmp/vc/in.raw' }
)
$log = "logs\upload_{0}.log" -f (Get-Date -Format 'yyyyMMdd_HHmmss')
$out = [System.Collections.Generic.List[string]]::new()
$swAll = [Diagnostics.Stopwatch]::StartNew()
foreach ($f in $files) {
    $sz = (Get-Item $f.Local).Length
    $msg = "=== {0} -> {1}  ({2:N0} bytes) ===" -f $f.Local, $f.Remote, $sz
    Write-Host $msg -ForegroundColor Cyan
    $out.Add($msg)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\upload_board.ps1 `
        -LocalFile $f.Local -RemotePath $f.Remote *>&1 | Tee-Object -Variable lines | Out-Null
    $sw.Stop()
    $txt = ($lines | Out-String)
    $out.Add($txt)
    $out.Add(("elapsed {0:N1} s  ({1:N2} KB/s binary)" -f $sw.Elapsed.TotalSeconds, ($sz / 1024.0 / $sw.Elapsed.TotalSeconds)))
    if ($txt -notmatch 'UPLOAD_VERIFIED') { throw "upload failed for $($f.Local)" }
    Write-Host ("  ok  {0:N1} s" -f $sw.Elapsed.TotalSeconds) -ForegroundColor Green
}
$swAll.Stop()
$out.Add(("ALL_UPLOADED  total {0:N1} s" -f $swAll.Elapsed.TotalSeconds))
$out | Set-Content -Path $log -Encoding utf8
Write-Host ("ALL_UPLOADED in {0:N1} s   log={1}" -f $swAll.Elapsed.TotalSeconds, $log) -ForegroundColor Green
