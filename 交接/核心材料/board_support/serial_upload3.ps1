param(
    [Parameter(Mandatory=$true)][string]$LocalPath,
    [Parameter(Mandatory=$true)][string]$RemotePath,
    [string]$PortName='COM8',
    [switch]$Executable
)
$ErrorActionPreference='Stop'
if ($RemotePath -notmatch '^/[a-zA-Z0-9_./-]+$') { throw 'Unsupported remote path' }
$expected=(Get-FileHash -LiteralPath $LocalPath -Algorithm SHA256).Hash.ToLowerInvariant()
$encoded=[Convert]::ToBase64String([IO.File]::ReadAllBytes($LocalPath))
$blen=$encoded.Length
$port=[IO.Ports.SerialPort]::new($PortName,115200,[IO.Ports.Parity]::None,8,[IO.Ports.StopBits]::One)
$port.Handshake=[IO.Ports.Handshake]::None
$port.WriteTimeout=30000
$port.ReadTimeout=500
function Drain($ms) {
    $deadline=[DateTime]::UtcNow.AddMilliseconds($ms); $text=''
    while ([DateTime]::UtcNow -lt $deadline) {
        try { $t=$port.ReadExisting(); $text+=$t } catch {}
        Start-Sleep -Milliseconds 20
    }
    return $text
}
try {
    $port.Open()
    $port.Write("`r"); Start-Sleep -Milliseconds 300
    if ((Drain 300) -notmatch 'root@[^\r\n]+[#$]') { throw 'Root shell not ready' }
    $py="import sys,base64,hashlib; d=sys.stdin.buffer.read($blen); blob=base64.b64decode(d); open('$RemotePath','wb').write(blob); print('VOICE_SHA='+hashlib.sha256(blob).hexdigest(),flush=True)"
    $shellPy="'"+$py.Replace("'", "'"+'"'+"'"+'"'+"'")+"'"
    $port.Write("stty -echo -icanon -ixon -ixoff -crtscts min 1 time 0; python3 -c $shellPy`r")
    Start-Sleep -Milliseconds 1200
    $ready = Drain 200
    if ($ready -match 'Traceback|Error') { throw "receiver error: $ready" }
    $chunk=1024; $total=$blen; $sent=0
    while ($sent -lt $total) {
        $n=[Math]::Min($chunk,$total-$sent)
        $port.Write($encoded.Substring($sent,$n))
        $sent+=$n
        Start-Sleep -Milliseconds 95
        if ($sent % 65536 -lt $chunk) { Write-Output ("progress {0:P0}" -f ($sent/$total)) }
    }
    $resp=Drain 4000
    if ($resp -notmatch [regex]::Escape($expected)) { throw "checksum mismatch: $resp" }
    if ($Executable) {
        $port.Write("stty sane; chmod 755 $RemotePath`r"); Start-Sleep -Milliseconds 400; Drain 200 | Out-Null
    } else {
        $port.Write("stty sane`r"); Start-Sleep -Milliseconds 300; Drain 200 | Out-Null
    }
    Write-Output "UPLOAD_VERIFIED $RemotePath SHA256=$expected"
}
finally {
    if ($port.IsOpen) { $port.Close() }
}
