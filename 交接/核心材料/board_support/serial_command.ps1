param(
    [Parameter(Mandatory = $true)]
    [string]$Command,
    [string]$PortName = "COM8",
    [int]$BootWaitSeconds = 30,
    [int]$ResponseMilliseconds = 3000
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
        $allText += Read-SerialFor 500
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

    $port.Write("$Command`r")
    [void](Read-SerialFor $ResponseMilliseconds)
}
finally {
    if ($port.IsOpen) {
        $port.Close()
    }
}
