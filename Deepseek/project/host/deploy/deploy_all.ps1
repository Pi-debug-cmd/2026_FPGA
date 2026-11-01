# deploy_all.ps1 - one command from "board is on the desk" to "results downloaded".
#
# Runs, in order, from the staging dir created by stage.ps1:
#   1. board_preflight.ps1      system facts, stop the sound-card demo, make /tmp/vc
#   2. board_upload_all.ps1     vc_stream + blob + 4 s input, per-file SHA check
#   3. board_run.ps1            4 s main chain + --nopitch control + dumps
#   4. board_download_results.ps1  pull outputs and dumps back
#
# Every step is the *already verified* script; this file only sequences it and
# stops on the first non-zero exit.  It has NOT been re-run end-to-end after
# packaging (the individual steps have), so treat a failure here as "check which
# step failed" rather than "the package is broken".
#
#   .\deploy_all.ps1 -Stage D:\vc_stage_20261026
param(
    [string]$Stage = 'D:\vc_stage_20261026',
    [string]$PortName = 'COM8',
    [switch]$SkipDownload
)
$ErrorActionPreference = 'Stop'
$tools = Join-Path $Stage 'tools'
if (-not (Test-Path $tools)) { throw "no staging dir: $Stage (run stage.ps1 first)" }

function Step($name, $script, $extra) {
    Write-Host "`n===== $name =====" -ForegroundColor Cyan
    $args = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $tools $script))
    if ($extra) { $args += $extra }
    Push-Location $Stage
    try { & powershell @args; $rc = $LASTEXITCODE }
    finally { Pop-Location }
    if ($rc -ne 0) { throw "$name failed (rc=$rc)" }
}

Write-Host "== serial port check =="
$port = [System.IO.Ports.SerialPort]::GetPortNames()
if ($port -notcontains $PortName) {
    throw "$PortName not present (found: $($port -join ', ')); close any serial terminal first"
}
Write-Host "  $PortName present"

Step 'preflight' 'board_preflight.ps1' $null
Step 'upload'    'board_upload_all.ps1' $null
Step 'run'       'board_run.ps1' $null
if (-not $SkipDownload) { Step 'download' 'board_download_results.ps1' $null }

Write-Host "`n[deploy_all] done. Logs in $Stage\logs" -ForegroundColor Green
Write-Host "Remember to restore the board (documented in docs/hardware_setup.md):"
Write-Host "  alsactl restore, stty echo, /etc/init.d/world-voice start"
