param(
    [Parameter(Mandatory = $true)][string]$LocalFile,
    [Parameter(Mandatory = $true)][string]$RemotePath,
    [string]$PortName = "COM9",
    [int]$BaudRate = 115200,
    [int]$ChunkChars = 8000,
    [int]$BootWaitSeconds = 20
)

$ErrorActionPreference = "Stop"
$bytes = [System.IO.File]::ReadAllBytes($LocalFile)
$b64all = [Convert]::ToBase64String($bytes)
$expectedSha = (Get-FileHash $LocalFile -Algorithm SHA256).Hash.ToLower()
# wrap base64 at 76 columns
$lines = New-Object System.Collections.Generic.List[string]
for ($i = 0; $i -lt $b64all.Length; $i += 76) {
    $end = [Math]::Min(76, $b64all.Length - $i)
    $lines.Add($b64all.Substring($i, $end))
}
$b64text = ($lines -join "`n") + "`n"
Write-Host "Encoded $($bytes.Length) bytes -> $($b64text.Length) base64 chars, expected sha $expectedSha"

$port = [System.IO.Ports.SerialPort]::new($PortName, $BaudRate, [System.IO.Ports.Parity]::None, 8, [System.IO.Ports.StopBits]::One)
$port.Handshake = [System.IO.Ports.Handshake]::None
$port.ReadTimeout = 300
$port.WriteTimeout = 5000
$script:rx = ""
function Drain([int]$ms) {
    $until = [DateTime]::UtcNow.AddMilliseconds($ms)
    while ([DateTime]::UtcNow -lt $until) {
        try { $t = $port.ReadExisting() } catch { $t = "" }
        if ($t.Length -gt 0) { $script:rx += $t; Write-Host -NoNewline $t }
        Start-Sleep -Milliseconds 30
    }
}
function Wait-Pattern([string]$pat, [int]$timeoutSec) {
    $dl = [DateTime]::UtcNow.AddSeconds($timeoutSec)
    while ([DateTime]::UtcNow -lt $dl) {
        try { $t = $port.ReadExisting() } catch { $t = "" }
        if ($t.Length -gt 0) { $script:rx += $t }
        if ($script:rx -match $pat) { return $true }
        Start-Sleep -Milliseconds 40
    }
    return $false
}

try {
    $port.Open()
    $port.Write("`r")
    $dl = [DateTime]::UtcNow.AddSeconds($BootWaitSeconds); $tail = ""; $in = $false
    while ([DateTime]::UtcNow -lt $dl -and -not $in) {
        $t = $port.ReadExisting()
        if ($t.Length -gt 0) { $tail += $t }
        if ($tail.Length -gt 400) { $tail = $tail.Substring($tail.Length - 400) }
        if ($tail -match "login:\s*$") { $port.Write("root`r"); Start-Sleep -Milliseconds 300; $tail = ""; continue }
        if ($tail -match "[#\$]\s*$") { $in = $true; break }
        Start-Sleep -Milliseconds 100; $port.Write("`r")
    }
    if (-not $in) { throw "no prompt" }
    Drain 300

    $b64remote = "$RemotePath.b64"
    $port.Write("rm -f $b64remote $RemotePath ; echo RDY=`$?`r")
    if (-not (Wait-Pattern 'RDY=0' 10)) { throw "rm failed" }
    Drain 200

    $total = $b64text.Length
    $pos = 0
    $idx = 0
    while ($pos -lt $total) {
        $idx++
        $len = [Math]::Min($ChunkChars, $total - $pos)
        $chunk = $b64text.Substring($pos, $len)
        # trim so chunk ends on a full line boundary
        if (($pos + $len) -lt $total) {
            $nl = $chunk.LastIndexOf("`n")
            if ($nl -gt 0) { $chunk = $chunk.Substring(0, $nl + 1); $len = $chunk.Length }
        }
        $port.Write("cat >> $b64remote <<'BEOF'`r")
        Start-Sleep -Milliseconds 150
        $port.Write(($chunk -replace "`n", "`r"))
        Start-Sleep -Milliseconds 150
        $mk = "CK$idx"
        $port.Write("BEOF`r")
        Start-Sleep -Milliseconds 100
        $port.Write("echo $mk=`$?`r")
        if (-not (Wait-Pattern "$mk=0" 60)) { throw "chunk $idx no ack" }
        $pos += $len
        Write-Host "`n--- chunk $idx sent, $pos / $total ---`n"
    }

    $port.Write("base64 -d $b64remote > $RemotePath ; echo DEC=`$?`r")
    if (-not (Wait-Pattern 'DEC=0' 60)) { throw "decode failed" }
    $script:rx = ""
    $port.Write("sha256sum $RemotePath | cut -c 1-64`r")
    if (-not (Wait-Pattern '[0-9a-f]{64}' 30)) { throw "no sha response" }
    $m = [regex]::Match($script:rx, '[0-9a-f]{64}')
    $boardSha = $m.Value
    Write-Host "`nBoard sha: $boardSha"
    if ($boardSha -ne $expectedSha) { throw "SHA MISMATCH board=$boardSha pc=$expectedSha" }
    Write-Host "UPLOAD_VERIFIED"
}
finally {
    if ($port.IsOpen) { $port.Close() }
}
