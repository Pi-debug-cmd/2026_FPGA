param(
    [Parameter(Mandatory = $true)]
    [string]$Command,
    [string]$PortName = "COM9",
    [int]$TimeoutSeconds = 30,
    [string]$LogPath = "",
    [int]$BaudRate = 115200,
    [int]$BootWaitSeconds = 20
)

$ErrorActionPreference = "Stop"
$port = [System.IO.Ports.SerialPort]::new(
    $PortName, $BaudRate,
    [System.IO.Ports.Parity]::None, 8,
    [System.IO.Ports.StopBits]::One
)
$port.Handshake = [System.IO.Ports.Handshake]::None
$port.ReadTimeout = 200
$port.WriteTimeout = 2000

$marker = "XDONE" + (Get-Random -Maximum 999999).ToString("000000")
$transcript = ""

function Append-Text([string]$t) {
    if ($t.Length -gt 0) {
        $script:transcript += $t
        Write-Host -NoNewline $t
    }
}

try {
    $port.Open()
    # Obtain a login shell / prompt
    $port.Write("`r")
    $deadline = [DateTime]::UtcNow.AddSeconds($BootWaitSeconds)
    $tail = ""
    $loggedIn = $false
    while ([DateTime]::UtcNow -lt $deadline -and -not $loggedIn) {
        $part = $port.ReadExisting()
        if ($part.Length -gt 0) { Append-Text $part; $tail += $part }
        if ($tail.Length -gt 400) { $tail = $tail.Substring($tail.Length - 400) }
        if ($tail -match "login:\s*$") {
            $port.Write("root`r"); Start-Sleep -Milliseconds 300; $tail = ""; continue
        }
        if ($tail -match "Password:\s*$") {
            $port.Write("root`r"); Start-Sleep -Milliseconds 300; $tail = ""; continue
        }
        if ($tail -match "[#\$]\s*$") {
            $loggedIn = $true; break
        }
        Start-Sleep -Milliseconds 100
        $port.Write("`r")
    }
    if (-not $loggedIn) {
        throw "No root shell prompt obtained within $BootWaitSeconds s."
    }

    # Quiet the prompt echo issues: send command followed by marker echo with exit code
    $full = "$Command ; echo ""$marker=`$?"""
    $port.Write($full + "`r")

    $cmdDeadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $found = $false
    while ([DateTime]::UtcNow -lt $cmdDeadline) {
        $part = $port.ReadExisting()
        if ($part.Length -gt 0) { Append-Text $part }
        if ($transcript -match [regex]::Escape($marker) + "=(-?\d+)") {
            $found = $true
            $script:exitCode = [int]$Matches[1]
            break
        }
        Start-Sleep -Milliseconds 50
    }
    if (-not $found) {
        Write-Host ""
        Write-Warning "Command did not finish within $TimeoutSeconds s (timeout)."
        $script:exitCode = 124
    } else {
        # drain a little so prompt returns
        $drainUntil = [DateTime]::UtcNow.AddMilliseconds(400)
        while ([DateTime]::UtcNow -lt $drainUntil) {
            $part = $port.ReadExisting()
            if ($part.Length -gt 0) { Append-Text $part }
            Start-Sleep -Milliseconds 50
        }
    }
}
finally {
    if ($port.IsOpen) { $port.Close() }
}

if ($LogPath -ne "") {
    $dir = Split-Path -Parent $LogPath
    if ($dir -ne "" -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $header = "==== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') PORT=$PortName CMD: $Command ====`r`n"
    [System.IO.File]::WriteAllText($LogPath, $header + $transcript + "`r`n[exit=$($script:exitCode)]`r`n", (New-Object System.Text.UTF8Encoding($false)))
}

Write-Host ""
Write-Host "[exit=$($script:exitCode)]"
exit $script:exitCode
