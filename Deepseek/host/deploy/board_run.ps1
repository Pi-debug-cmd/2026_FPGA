# Run vc_stream on the board and capture telemetry + stage dumps.
#
#   .\tools\board_run.ps1                 # full chain + --nopitch control, plus dumps
#   .\tools\board_run.ps1 -Seconds 4 -Extra "--nopitch"
#
# Everything happens under /tmp/vc; the sound-card demo is stopped first because
# the audio device is single-subdevice and must be idle.
param(
    [string]$PortName = 'COM8',
    [double]$Seconds = 4,
    [string]$RemoteDir = '/tmp/vc',
    [switch]$SkipStop
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root
. .\tools\serial_lib.ps1
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$log = "logs\board_run_$stamp.log"
$sb = [System.Text.StringBuilder]::new()
function Rec($s) { Write-Host $s; [void]$sb.AppendLine($s) }

$p = Connect-Board -PortName $PortName
try {
    if (-not $SkipStop) {
        Rec "== stop world-voice (frees the only pcm subdevice) =="
        Rec (Invoke-BoardCmd $p "/etc/init.d/world-voice stop 2>&1; echo rc=`$?" -TimeoutSec 60 -Quiet).Output
    }
    Rec "== inventory =="
    Rec (Invoke-BoardCmd $p "cd $RemoteDir && ls -l; echo ---; sha256sum vc_stream student_v5.blob in.raw" -Quiet).Output
    Rec (Invoke-BoardCmd $p "free -m | head -2" -Quiet).Output

    # ---- run 1: full chain, stage dumps on
    Rec "== run 1: pitch 1.40, dumps to /tmp/vc/dump =="
    $cmd = "cd $RemoteDir && rm -rf dump && mkdir -p dump && t0=`$(date +%s%N); " +
           "./vc_stream $Seconds native_s24 200 --dump dump < in.raw > out.raw 2> tel1.json; rc=`$?; " +
           "t1=`$(date +%s%N); echo RC=`$rc; echo WALL_MS=`$(( (t1-t0)/1000000 )); echo ---TEL---; cat tel1.json"
    Rec (Invoke-BoardCmd $p $cmd -TimeoutSec 300).Output
    Rec (Invoke-BoardCmd $p "cd $RemoteDir && ls -l out.raw dump | head -20" -Quiet).Output

    # ---- run 2: no-pitch control (the Python "A" path)
    Rec "== run 2: --nopitch control =="
    $cmd2 = "cd $RemoteDir && t0=`$(date +%s%N); " +
            "./vc_stream $Seconds native_s24 200 --nopitch --dump dump_np < in.raw > out_np.raw 2> tel2.json; rc=`$?; " +
            "t1=`$(date +%s%N); echo RC=`$rc; echo WALL_MS=`$(( (t1-t0)/1000000 )); echo ---TEL---; cat tel2.json"
    Rec (Invoke-BoardCmd $p $cmd2 -TimeoutSec 300).Output

    # ---- run 3: repeat of run 1 for timing stability
    Rec "== run 3: repeat timing =="
    $cmd3 = "cd $RemoteDir && t0=`$(date +%s%N); " +
            "./vc_stream $Seconds native_s24 200 < in.raw > /dev/null 2> tel3.json; rc=`$?; " +
            "t1=`$(date +%s%N); echo RC=`$rc; echo WALL_MS=`$(( (t1-t0)/1000000 )); echo ---TEL---; cat tel3.json"
    Rec (Invoke-BoardCmd $p $cmd3 -TimeoutSec 300).Output

    # ---- output level / header check of the raw result
    Rec "== out.raw sanity =="
    Rec (Invoke-BoardCmd $p "cd $RemoteDir && wc -c out.raw out_np.raw && sha256sum out.raw" -Quiet).Output

    # ---- run 4: a genuine 32 kHz capture from the on-board codec, no upload
    Rec "== run 4: arecord 4 s from hw:0,1 then convert (real capture path) =="
    Rec (Invoke-BoardCmd $p "cat /proc/asound/card0/pcm1c/sub0/status 2>/dev/null | head -2" -Quiet).Output
    Rec (Invoke-BoardCmd $p "cd $RemoteDir && arecord -v -D hw:0,1 -t raw -f S24_LE -r 32000 -c 2 --period-size=512 --buffer-size=4096 -d 4 mic.raw 2>&1 | tail -5; echo AREC_RC=`$?; wc -c mic.raw" -TimeoutSec 120).Output
    $cmd4 = "cd $RemoteDir && t0=`$(date +%s%N); " +
            "./vc_stream 4 native_s24 200 < mic.raw > out_mic.raw 2> tel4.json; rc=`$?; " +
            "t1=`$(date +%s%N); echo RC=`$rc; echo WALL_MS=`$(( (t1-t0)/1000000 )); echo ---TEL---; cat tel4.json"
    Rec (Invoke-BoardCmd $p $cmd4 -TimeoutSec 300).Output
    Rec (Invoke-BoardCmd $p "cd $RemoteDir && wc -c out_mic.raw" -Quiet).Output
} finally {
    Close-Board $p
    $sb.ToString() | Set-Content -Path $log -Encoding utf8
    Write-Host "`nlog: $log"
}
