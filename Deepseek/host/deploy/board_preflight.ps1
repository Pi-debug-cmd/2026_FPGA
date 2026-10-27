# Board pre-flight: system facts, sound-card state, stop the autostart demo, and
# prepare /tmp/vc.  Only /tmp/ is written; no system file is touched.
#
#   .\tools\board_preflight.ps1
param([string]$PortName = 'COM8', [switch]$RestartDemo)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root
. .\tools\serial_lib.ps1
$log = "logs\preflight_{0}.log" -f (Get-Date -Format 'yyyyMMdd_HHmmss')
$sb = [System.Text.StringBuilder]::new()
function Rec($s) { Write-Host $s; [void]$sb.AppendLine($s) }

$p = Connect-Board -PortName $PortName
try {
    Rec "== uname / memory / time =="
    Rec (Invoke-BoardCmd $p "uname -a; date" -Quiet).Output
    Rec (Invoke-BoardCmd $p "free -m | head -3" -Quiet).Output
    Rec "== glibc =="
    Rec (Invoke-BoardCmd $p "ldd --version 2>&1 | head -1" -Quiet).Output
    Rec "== sound card =="
    Rec (Invoke-BoardCmd $p "aplay -l 2>&1 | head -8" -Quiet).Output
    Rec "== pcm owner pids =="
    Rec (Invoke-BoardCmd $p "cat /proc/asound/card0/pcm0p/sub0/status 2>/dev/null | head -4; cat /proc/asound/card0/pcm1c/sub0/status 2>/dev/null | head -4" -Quiet).Output
    Rec "== stop demo =="
    Rec (Invoke-BoardCmd $p "/etc/init.d/world-voice stop; echo rc=`$?" -TimeoutSec 60).Output
    Start-Sleep -Seconds 2
    Rec (Invoke-BoardCmd $p "ps | grep -E 'arecord|aplay|world' | grep -v grep | head -5; echo ---" -Quiet).Output
    Rec (Invoke-BoardCmd $p "cat /proc/asound/card0/pcm0p/sub0/status 2>/dev/null | head -2; cat /proc/asound/card0/pcm1c/sub0/status 2>/dev/null | head -2" -Quiet).Output
    Rec "== prepare /tmp/vc =="
    Rec (Invoke-BoardCmd $p "mkdir -p /tmp/vc; ls -ld /tmp/vc; df -h /tmp | tail -1" -Quiet).Output
    Rec "== free space on the root filesystem =="
    Rec (Invoke-BoardCmd $p "df -m / | tail -1" -Quiet).Output
    if ($RestartDemo) {
        Rec (Invoke-BoardCmd $p "/etc/init.d/world-voice start; echo rc=`$?" -TimeoutSec 60).Output
    }
} finally {
    Close-Board $p
    $sb.ToString() | Set-Content -Path $log -Encoding utf8
    Write-Host "`nlog: $log"
}
