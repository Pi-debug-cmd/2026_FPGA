param(
    [Parameter(Mandatory=$true)][string]$RemotePath,
    [Parameter(Mandatory=$true)][string]$LocalPath,
    [string]$PortName='COM8'
)
$ErrorActionPreference='Stop'
if ($RemotePath -notmatch '^/[a-zA-Z0-9_./-]+$') { throw 'Unsupported remote path' }
$port=[System.IO.Ports.SerialPort]::new($PortName,115200)
$port.ReadTimeout=400
$port.DtrEnable=$true
$port.WriteTimeout=10000
try {
    $port.Open()
    Start-Sleep -Milliseconds 300
    $port.Write([char]3); Start-Sleep -Milliseconds 300
    $port.Write("`r"); Start-Sleep -Milliseconds 300
    $port.ReadExisting() | Out-Null
    $tag = 'DLTAG_8d2z'
    $port.Write("echo; echo $tag; base64 -w 0 $RemotePath; echo; echo ${tag}_END`r")
    $all=''; $end=[DateTime]::UtcNow.AddSeconds(180)
    while([DateTime]::UtcNow -lt $end -and $all -notmatch "_END") {
        Start-Sleep -Milliseconds 30
        $all += $port.ReadExisting()
    }
    Start-Sleep -Milliseconds 300
    $all += $port.ReadExisting()
    # Strip ANSI
    $all = [regex]::Replace($all, '\x1b\[[0-9;?]*[A-Za-z]', '')
    $m = [regex]::Match($all, "(?s)$tag\r?\n(.*?)\r?\n${tag}_END")
    if (-not $m.Success) { throw "framing failed; tail=" + $all.Substring([Math]::Max(0,$all.Length-200)) }
    $b64 = [regex]::Replace($m.Groups[1].Value, '\s', '')
    $bytes=[Convert]::FromBase64String($b64)
    [IO.File]::WriteAllBytes($LocalPath,$bytes)
    Write-Output "DOWNLOAD_VERIFIED $RemotePath -> $LocalPath bytes=$($bytes.Length)"
}
finally {
    $port.Close()
}
