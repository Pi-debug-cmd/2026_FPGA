# Pull the board results back: the S24 output plus the three stage dumps that the
# comparison needs.  One file at a time (COM8 is exclusive).
#   .\tools\board_download_results.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root
$dest = 'out\board_final'
New-Item -ItemType Directory -Force -Path $dest, "$dest\dump" | Out-Null
$files = @(
    @{ Remote = '/tmp/vc/fin4/out.raw';        Local = "$dest\out.raw" },
    @{ Remote = '/tmp/vc/fin4/x16.f32';   Local = "$dest\dump\x16.f32" },
    @{ Remote = '/tmp/vc/fin4/xb16.f32';  Local = "$dest\dump\xb16.f32" },
    @{ Remote = '/tmp/vc/fin4/y16.f32';   Local = "$dest\dump\y16.f32" }
)
$log = "logs\download_{0}.log" -f (Get-Date -Format 'yyyyMMdd_HHmmss')
$out = [System.Collections.Generic.List[string]]::new()
$swAll = [Diagnostics.Stopwatch]::StartNew()
foreach ($f in $files) {
    Write-Host ("=== {0} -> {1} ===" -f $f.Remote, $f.Local) -ForegroundColor Cyan
    & powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\download_board.ps1 `
        -RemotePath $f.Remote -LocalPath $f.Local *>&1 | Tee-Object -Variable lines | Out-Null
    $txt = ($lines | Out-String)
    $out.Add($txt)
    if ($txt -notmatch 'DOWNLOAD_VERIFIED') { throw "download failed for $($f.Remote)" }
    Write-Host $txt.Trim() -ForegroundColor Green
}
$swAll.Stop()
$out.Add(("ALL_DOWNLOADED total {0:N1} s" -f $swAll.Elapsed.TotalSeconds))
$out | Set-Content -Path $log -Encoding utf8
Write-Host ("ALL_DOWNLOADED in {0:N1} s  log={1}" -f $swAll.Elapsed.TotalSeconds, $log) -ForegroundColor Green
