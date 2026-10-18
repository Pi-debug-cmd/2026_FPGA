param(
    [Parameter(Mandatory=$true)][string]$LocalFile,
    [Parameter(Mandatory=$true)][string]$RemotePath,
    [string]$PortName='COM14',
    [switch]$RecoverInterruptedTransfer
)
$ErrorActionPreference='Stop'
if ($RemotePath -notmatch '^/tmp/codex_[a-zA-Z0-9_./-]+$' -or $RemotePath -match '(^|/)\.\.(/|$)') { throw 'Only project /tmp paths are supported' }
$source=[System.IO.File]::ReadAllBytes($LocalFile)
$sha=[System.Security.Cryptography.SHA256]::Create()
function Hash-Bytes([byte[]]$data, [int]$count) {
    ([BitConverter]::ToString($sha.ComputeHash($data,0,$count))).Replace('-','').ToLowerInvariant()
}
$expected=Hash-Bytes $source $source.Length
$encoded=[Convert]::ToBase64String($source)
$lines=[System.Collections.Generic.List[string]]::new()
for ($i=0;$i -lt $encoded.Length;$i+=76) { $lines.Add($encoded.Substring($i,[Math]::Min(76,$encoded.Length-$i))) }
$payload=[System.Text.Encoding]::ASCII.GetBytes(($lines -join "`n")+"`n")
$port=[System.IO.Ports.SerialPort]::new($PortName,115200)
$port.DtrEnable=$false
$port.RtsEnable=$false
$port.WriteTimeout=5000
$receiverStarted=$false
function Read-Match([string]$pattern,[int]$seconds=15) {
    $buffer=''
    $deadline=[DateTime]::UtcNow.AddSeconds($seconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        $buffer+=$port.ReadExisting()
        $match=[regex]::Match($buffer,$pattern)
        if ($match.Success) { return $match }
        Start-Sleep -Milliseconds 20
    }
    $receivedTail = $buffer.Substring([Math]::Max(0, $buffer.Length - 600))
    throw ('Transfer response timed out; received tail: ' + $receivedTail)
}
$receiver=@'
import base64,hashlib,os,sys,termios
p='REMOTE_PATH'
expected='EXPECTED_SHA'
os.makedirs(os.path.dirname(p),exist_ok=True)
fd=sys.stdin.fileno()
original=termios.tcgetattr(fd)
attrs=termios.tcgetattr(fd)
attrs[3]&=~(termios.ECHO|termios.ICANON)
attrs[6][termios.VMIN]=1
attrs[6][termios.VTIME]=0
termios.tcsetattr(fd,termios.TCSANOW,attrs)
try:
    prefix=open(p+'.b64','rb').read() if os.path.exists(p+'.b64') else b''
    offset=len(prefix)
    print('PREFIX:%d:%s'%(offset,hashlib.sha256(prefix).hexdigest()),flush=True)
    with open(p+'.b64','ab') as f:
        while True:
            header=sys.stdin.buffer.readline().decode().strip()
            if header=='FINISH':break
            assert header.startswith('SIZE:')
            size=int(header[5:])
            assert 0<size<=4096
            block=sys.stdin.buffer.read(size)
            assert len(block)==size
            f.write(block);f.flush();offset+=size
            print('ACK:%d'%offset,flush=True)
    raw=base64.b64decode(open(p+'.b64','rb').read())
    digest=hashlib.sha256(raw).hexdigest()
    assert digest==expected,'Decoded checksum mismatch'
    with open(p+'.incoming','wb') as f:f.write(raw)
    os.replace(p+'.incoming',p)
    print('VERIFIED:%d:%s'%(len(raw),digest),flush=True)
finally:
    termios.tcsetattr(fd,termios.TCSANOW,original)
'@
$receiver=$receiver.Replace('REMOTE_PATH',$RemotePath).Replace('EXPECTED_SHA',$expected)
$code=[Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($receiver))
try {
    $port.Open()
    # Ctrl+C is allowed only to recover this project's interrupted receiver.
    if ($RecoverInterruptedTransfer) { $port.Write([string][char]3); Start-Sleep -Milliseconds 500; $null=$port.ReadExisting() }
    $port.Write("`r")
    $null=Read-Match '(?m)#[^\r\n]*$'
    $command='/usr/bin/python3 -c ''import base64;exec(base64.b64decode("'+$code+'"))'''
    $port.Write($command+"`r")
    $receiverStarted=$true
    $prefix=Read-Match '(?m)^PREFIX:(\d+):([0-9a-f]{64})\r?$'
    $offset=[int]$prefix.Groups[1].Value
    if ($offset -gt $payload.Length -or $prefix.Groups[2].Value -ne (Hash-Bytes $payload $offset)) { throw 'Existing prefix differs from local data' }
    Write-Output "RESUME_VERIFIED encoded_offset=$offset total=$($payload.Length)"
    $nextReport=$offset+262144
    while ($offset -lt $payload.Length) {
        $count=[Math]::Min(4096,$payload.Length-$offset)
        $port.Write("SIZE:$count`n")
        $port.Write($payload,$offset,$count)
        $offset+=$count
        $ack=Read-Match '(?m)^ACK:(\d+)\r?$'
        if ([int]$ack.Groups[1].Value -ne $offset) { throw 'Transfer offset mismatch' }
        if ($offset -ge $nextReport) { Write-Output "TRANSFER_PROGRESS $offset/$($payload.Length)"; $nextReport=$offset+262144 }
    }
    $port.Write("FINISH`n")
    $done=Read-Match '(?m)^VERIFIED:(\d+):([0-9a-f]{64})\r?$' 30
    if ([int]$done.Groups[1].Value -ne $source.Length -or $done.Groups[2].Value -ne $expected) { throw 'Final verification mismatch' }
    $receiverStarted=$false
    Write-Output "UPLOAD_VERIFIED bytes=$($source.Length) sha256=$expected"
} finally {
    if ($port.IsOpen) {
        if ($receiverStarted) { $port.Write([string][char]3); Start-Sleep -Milliseconds 300 }
        $port.Close()
    }
    $sha.Dispose()
}
