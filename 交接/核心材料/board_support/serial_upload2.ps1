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
    $probe = Drain 300
    if ($probe -notmatch 'root@[^\r\n]+[#$]') { throw 'Root shell not ready' }
    $py="import sys,base64,hashlib; d=b'';`nwhile b'\n' not in d: d+=sys.stdin.buffer.read(8192)`nb=d.split(b'\n',1)[0]; blob=base64.b64decode(b''.join(d.split(b'\n')[:1]) if False else b); open('$RemotePath','wb').write(blob); print('VOICE_SHA='+hashlib.sha256(blob).hexdigest(),flush=True)"
    $py="import sys,base64,hashlib; d=b''`nwhile b'\n' not in d: d+=sys.stdin.buffer.read(8192)`nb=d.split(b'\n',1)[0]; blob=base64.b64decode(b); open('$RemotePath','wb').write(blob); print('VOICE_SHA='+hashlib.sha256(blob).hexdigest(),flush=True)"
    $shellPy="'"+$py.Replace("'", "'"+'"'+"'"+'"'+"'")+"'"
    $port.Write("stty -echo -icanon min 1 time 0; python3 -c $shellPy`r")
    Start-Sleep -Milliseconds 1200
    $ready = Drain 300
    if ($ready -match 'Traceback|Error') { throw "receiver error: $ready" }
    # Send base64 + newline in chunks paced to the line rate (~11.5 KB/s).
    $payload = $encoded + "`n"
    $chunk = 2048
    $total = $payload.Length; $sent = 0
    while ($sent -lt $total) {
        $n = [Math]::Min($chunk, $total-$sent)
        $port.Write($payload.Substring($sent,$n))
        $sent += $n
        # 2048 bytes take ~178ms at 115200; wait a touch more.
        Start-Sleep -Milliseconds 200
        $back = Drain 20
        if ($back -match 'VOICE_SHA=') { break }
        if ($back -match 'Traceback|Error') { throw "receiver error: $back" }
        if ($sent % 65536 -eq 0) { Write-Output ("progress {0:P0}" -f ($sent/$total)) }
    }
    $resp = Drain 3000
    $all = $back + $resp
    if ($all -notmatch [regex]::Escape($expected)) { throw "checksum mismatch: $all" }
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
