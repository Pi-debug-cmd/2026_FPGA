param(
    [string]$PortName = "COM9",
    [int]$BaudRate = 115200,
    [int]$WaitSeconds = 15
)
$ErrorActionPreference = "Stop"
$port = [System.IO.Ports.SerialPort]::new(
    $PortName, $BaudRate,
    [System.IO.Ports.Parity]::None, 8,
    [System.IO.Ports.StopBits]::One
)
$port.Handshake = [System.IO.Ports.Handshake]::None
$port.ReadTimeout = 200
try {
    $port.Open()
    # Abort any unfinished heredoc / quoted input with Ctrl-C, then Enter.
    foreach ($i in 1..3) {
        $port.Write([char]3)
        Start-Sleep -Milliseconds 200
        $port.Write("`r")
        Start-Sleep -Milliseconds 300
    }
    $deadline = [DateTime]::UtcNow.AddSeconds($WaitSeconds)
    $tail = ""
    $ok = $false
    while ([DateTime]::UtcNow -lt $deadline) {
        $part = $port.ReadExisting()
        if ($part.Length -gt 0) { Write-Host -NoNewline $part; $tail += $part }
        if ($tail.Length -gt 300) { $tail = $tail.Substring($tail.Length - 300) }
        if ($tail -match "[#\$]\s*$") { $ok = $true; break }
        Start-Sleep -Milliseconds 150
        $port.Write("`r")
    }
    Write-Host ""
    if ($ok) { Write-Host "PROMPT_RECOVERED" } else { Write-Host "PROMPT_NOT_FOUND"; exit 1 }
}
finally {
    if ($port.IsOpen) { $port.Close() }
}
