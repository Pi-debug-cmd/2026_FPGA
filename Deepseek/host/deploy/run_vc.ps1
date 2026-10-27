# Run vc_stream with file-based stdin/stdout/stderr.
# PowerShell has no `<` redirection for native commands, and the board contract is
# "raw PCM on stdin/stdout, JSON on stderr", so cmd.exe does the plumbing here.
#
#   .\tools\run_vc.ps1 -Exe build\vc_stream_host.exe `
#        -VcArgs "4 pcm16 0 --in-f32-16k --out-f32-16k --nopitch --dump out\c_nopitch" `
#        -In out\c_nopitch\x16.f32 -Out out\c_nopitch\y_out.f32 -Err out\c_nopitch\err.txt
param(
    [Parameter(Mandatory = $true)][string]$Exe,
    [Parameter(Mandatory = $true)][string]$VcArgs,
    [Parameter(Mandatory = $true)][string]$In,
    [Parameter(Mandatory = $true)][string]$Out,
    [string]$Err = "",
    [string]$WorkDir = ""
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path $Exe)) { throw "exe not found: $Exe" }
if (-not (Test-Path $In)) { throw "stdin file not found: $In" }
if (-not $Err) { $Err = [System.IO.Path]::ChangeExtension($Out, ".stderr.txt") }
foreach ($p in @($Out, $Err)) {
    $d = Split-Path -Parent $p
    if ($d -and -not (Test-Path $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
}
$cmd = "`"$Exe`" $VcArgs < `"$In`" > `"$Out`" 2> `"$Err`""
if ($WorkDir) { $cmd = "cd /d `"$WorkDir`" && $cmd" }
$sw = [Diagnostics.Stopwatch]::StartNew()
cmd /c $cmd
$rc = $LASTEXITCODE
$sw.Stop()
Write-Host ("rc={0}  wall={1:N0} ms  out={2:N0} B" -f $rc, $sw.Elapsed.TotalMilliseconds,
    (Get-Item $Out).Length) -ForegroundColor $(if ($rc -eq 0) { "Green" } else { "Red" })
if (Test-Path $Err) {
    $e = Get-Content $Err -Raw
    if ($e) { Write-Host $e.Trim() }
}
exit $rc
