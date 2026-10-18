param(
    [Parameter(Mandatory=$true)][string]$LocalPath,
    [Parameter(Mandatory=$true)][string]$RemotePath,
    [string]$PortName='COM8',
    [int]$ChunkBytes=2048
)
$ErrorActionPreference='Stop'
if ($RemotePath -notmatch '^/[a-zA-Z0-9_./-]+$') { throw 'Unsupported remote path' }
$expected=(Get-FileHash -LiteralPath $LocalPath -Algorithm SHA256).Hash.ToLowerInvariant()
$bytes=[IO.File]::ReadAllBytes($LocalPath)
$total=$bytes.Length

$port=[IO.Ports.SerialPort]::new($PortName,115200,[IO.Ports.Parity]::None,8,[IO.Ports.StopBits]::One)
$port.Handshake=[IO.Ports.Handshake]::None
$port.WriteTimeout=30000
$port.ReadTimeout=500
$port.DtrEnable=$true
$port.WriteBufferSize=8192

function Drain($ms) {
    $deadline=[DateTime]::UtcNow.AddMilliseconds($ms); $text=''
    while ([DateTime]::UtcNow -lt $deadline) {
        try { $t=$port.ReadExisting(); $text+=$t } catch {}
        Start-Sleep -Milliseconds 20
    }
    return $text
}
function WaitFor($pattern,$timeoutSec) {
    $all=''; $end=[DateTime]::UtcNow.AddSeconds($timeoutSec)
    while([DateTime]::UtcNow -lt $end){
        Start-Sleep -Milliseconds 40
        try { $all+=$port.ReadExisting() } catch {}
        if ($all -match $pattern) { return $all }
    }
    throw "timeout waiting for $pattern; got: $all"
}
try {
    $port.Open()
    $port.Write("`r"); Start-Sleep -Milliseconds 300
    if ((Drain 300) -notmatch 'root@[^\r\n]+[#$]') { throw 'Root shell not ready' }
    $py=@'
import sys,base64,hashlib
f=open("RP","wb"); h=hashlib.sha256(); n=0
while True:
    try:
        line=sys.stdin.buffer.readline()
        if not line:
            print("EOF",flush=True); break
        s=line.strip()
        if s==b"__END__": break
        blob=base64.b64decode(s)
        f.write(blob); h.update(blob); n+=1
        print("OK",flush=True)
    except Exception as e:
        print("ERR:"+repr(e),flush=True)
f.close()
print("SHA="+h.hexdigest(),flush=True)
'@
    $py=$py.Replace("RP",$RemotePath)
    $b64py=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($py))
    $port.Write("stty -echo -icanon -ixon -ixoff -crtscts; python3 -c 'import base64;exec(base64.b64decode(`"$b64py`"))'`r")
    Start-Sleep -Milliseconds 1500
    $ready=$port.ReadExisting()
    if ($ready -match 'Traceback|Error') { throw "receiver error: $ready" }

    $sent=0; $idx=0; $timingLog=@()
    while($sent -lt $total){
        $n=[Math]::Min($ChunkBytes,$total-$sent)
        $chunk=New-Object byte[] $n
        [Array]::Copy($bytes,$sent,$chunk,0,$n)
        $line=[Convert]::ToBase64String($chunk)
        $t0=[DateTime]::UtcNow
        $port.Write($line+"`n")
        $all=''; $end=[DateTime]::UtcNow.AddSeconds(15); $found=$false
        while([DateTime]::UtcNow -lt $end){
            Start-Sleep -Milliseconds 30
            try { $all+=$port.ReadExisting() } catch {}
            if ($all -match '(?m)^OK') { $found=$true; break }
            if ($all -match 'ERR:|EOF') { throw "receiver error: $all" }
        }
        if(-not $found){ throw "no OK; got: $all" }
        $el=[math]::Round(([DateTime]::UtcNow-$t0).TotalMilliseconds)
        $timingLog+="chunk $idx : ${el}ms"
        $sent+=$n; $idx++
        $timingLog | Set-Content 'D:\Tools_FPGA\msys_root\tmp\ack_timing.log' -Encoding UTF8
        if(($idx % 20) -eq 0){ Write-Output ("progress {0:P0}" -f ($sent/$total)) }
    }
    $port.Write("__END__`n")
    $fin=WaitFor 'SHA=[0-9a-f]{64}' 20
    $m=[regex]::Match($fin,'SHA=([0-9a-f]{64})')
    $got=$m.Groups[1].Value
    if($got -ne $expected){ throw "checksum mismatch: got $got expected $expected" }
    $port.Write("stty sane`r"); Start-Sleep -Milliseconds 400
    Write-Output "UPLOAD_VERIFIED $RemotePath SHA256=$expected"
}
finally {
    if($port.IsOpen){ $port.Close() }
}
