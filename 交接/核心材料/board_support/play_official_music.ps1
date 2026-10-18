param(
    [string]$PortName = "COM8",
    [int]$BootWaitSeconds = 45
)

$ErrorActionPreference = "Stop"
$port = [System.IO.Ports.SerialPort]::new(
    $PortName,
    115200,
    [System.IO.Ports.Parity]::None,
    8,
    [System.IO.Ports.StopBits]::One
)
$port.Handshake = [System.IO.Ports.Handshake]::None
$port.NewLine = "`r"
$port.ReadTimeout = 200
$port.WriteTimeout = 1000

function Read-SerialFor([int]$Milliseconds) {
    $deadline = [DateTime]::UtcNow.AddMilliseconds($Milliseconds)
    $text = ""
    while ([DateTime]::UtcNow -lt $deadline) {
        $part = $port.ReadExisting()
        if ($part.Length -gt 0) {
            $text += $part
            Write-Host -NoNewline $part
        }
        Start-Sleep -Milliseconds 50
    }
    return $text
}

try {
    $port.Open()
    $port.Write("`r")

    $deadline = [DateTime]::UtcNow.AddSeconds($BootWaitSeconds)
    $allText = ""
    $loggedIn = $false
    while ([DateTime]::UtcNow -lt $deadline -and -not $loggedIn) {
        $allText += Read-SerialFor 700

        if ($allText -match "login:\s*$") {
            $port.Write("root`r")
            $allText = ""
            continue
        }
        if ($allText -match "Password:\s*$") {
            $port.Write("root`r")
            $allText = ""
            continue
        }
        if ($allText -match "root@[^\r\n]+[#$]\s*$") {
            $loggedIn = $true
            break
        }

        if ($allText.Length -gt 8192) {
            $allText = $allText.Substring($allText.Length - 8192)
        }
        $port.Write("`r")
    }

    if (-not $loggedIn) {
        throw "The board did not reach a root shell within $BootWaitSeconds seconds."
    }

    $mixer = "amixer sset 'Headphone Playback ZC' on >/dev/null; " +
        "amixer sset 'Speaker Playback ZC' on >/dev/null; " +
        "amixer sset 'Right Output Mixer PCM' on >/dev/null; " +
        "amixer sset 'Left Output Mixer PCM' on >/dev/null; " +
        "amixer sset Headphone 105,105 >/dev/null; " +
        "amixer sset Speaker 118,118 >/dev/null; " +
        "amixer sset Playback 230,230 >/dev/null; " +
        "amixer sset 'Speaker AC' 3 >/dev/null; " +
        "amixer sset 'Speaker DC' 3 >/dev/null"
    $command = "pkill aplay 2>/dev/null; $mixer; aplay /opt/hardware_test/test.wav >/tmp/codex_aplay.log 2>&1 & echo MUSIC_STARTED_PID:`$!"
    $port.Write("$command`r")
    $response = Read-SerialFor 3000
    if ($response -notmatch "MUSIC_STARTED_PID:\d+") {
        throw "The board shell did not confirm that music started."
    }
}
finally {
    if ($port.IsOpen) {
        $port.Close()
    }
}
