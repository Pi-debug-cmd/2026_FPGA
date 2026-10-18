param(
    [Parameter(Mandatory=$true)][string]$RemotePath,
    [Parameter(Mandatory=$true)][string]$LocalPath,
    [string]$PortName='COM14'
)
$ErrorActionPreference='Stop'
if ($RemotePath -notmatch '^/[a-zA-Z0-9_./-]+$') { throw 'Unsupported remote path' }
$port=[System.IO.Ports.SerialPort]::new($PortName,115200)
$port.WriteTimeout=5000
$receiverStarted=$false
function Read-Match([string]$pattern, [int]$seconds=15) {
    $buffer=''
    $deadline=[DateTime]::UtcNow.AddSeconds($seconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        $buffer += $port.ReadExisting()
        $match=[regex]::Match($buffer,$pattern)
        if ($match.Success) { return $match }
        Start-Sleep -Milliseconds 20
    }
    throw "Timed out awaiting transfer response"
}
try {
    $port.Open()
    $port.Write("`r")
    Read-Match 'root@[^\r\n]+[#]' | Out-Null
    $source=@'
import sys,base64,hashlib
data=open("REMOTE_FILE","rb").read(); pos=0
print("READY",flush=True)
for line in sys.stdin.buffer:
    if line.strip()!=b"NEXT": continue
    chunk=data[pos:pos+4096]
    if not chunk:
        print("END:%d:%s"%(len(data),hashlib.sha256(data).hexdigest()),flush=True)
        break
    print("DATA:"+base64.b64encode(chunk).decode(),flush=True)
    pos+=len(chunk)
'@
    $source=$source.Replace('REMOTE_FILE',$RemotePath)
    $encoded=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($source))
    $port.Write("stty -echo -icanon; python3 -c 'import base64;exec(base64.b64decode(`"$encoded`"))'; stty sane`r")
    $receiverStarted=$true
    Read-Match '(?m)^READY\r?\n' | Out-Null
    $stream=[IO.MemoryStream]::new()
    try {
        while ($true) {
            $port.Write("NEXT`n")
            $match=Read-Match '(?m)^(DATA:([A-Za-z0-9+/=]+)|END:([0-9]+):([0-9a-f]{64}))\r?\n'
            if ($match.Groups[2].Success) {
                $bytes=[Convert]::FromBase64String($match.Groups[2].Value)
                $stream.Write($bytes,0,$bytes.Length)
            } else {
                $expectedSize=[long]$match.Groups[3].Value
                $expectedSha=$match.Groups[4].Value
                break
            }
        }
        $result=$stream.ToArray()
    } finally { $stream.Dispose() }
    $actualSha=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($result))).Replace('-','').ToLower()
    if ($result.Length -ne $expectedSize -or $actualSha -ne $expectedSha) { throw 'Download integrity mismatch' }
    $destination=[IO.Path]::GetFullPath($LocalPath)
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination)) | Out-Null
    [IO.File]::WriteAllBytes($destination,$result)
    $receiverStarted=$false
    Write-Output "DOWNLOAD_VERIFIED bytes=$expectedSize sha256=$actualSha"
} finally {
    if ($port.IsOpen) {
        if ($receiverStarted) { $port.Write([char]3); Start-Sleep -Milliseconds 100; $port.Write("stty sane`r") }
        $port.Close()
    }
}
