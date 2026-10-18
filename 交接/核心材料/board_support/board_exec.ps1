param(
    [Parameter(Mandatory=$true)][string]$Command,
    [string]$PortName='COM8',
    [int]$TimeoutSec=30
)
$port=[System.IO.Ports.SerialPort]::new($PortName,115200)
$port.ReadTimeout=400
$port.DtrEnable=$true
$port.Open()
try {
    Start-Sleep -Milliseconds 300
    $port.Write([char]3); Start-Sleep -Milliseconds 300
    $port.Write("`r"); Start-Sleep -Milliseconds 300
    $port.ReadExisting() | Out-Null
    $port.Write($Command + "`r")
    $all=''; $end=[DateTime]::UtcNow.AddSeconds($TimeoutSec)
    while([DateTime]::UtcNow -lt $end) {
        Start-Sleep -Milliseconds 150
        $all += $port.ReadExisting()
        if ($all -match 'CMD_END_9f3k') { break }
    }
    # Strip ANSI escape sequences
    $clean = [regex]::Replace($all, '\x1b\[[0-9;?]*[A-Za-z]', '')
    return $clean
}
finally {
    $port.Close()
}
