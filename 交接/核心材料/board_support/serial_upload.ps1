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
$port.WriteTimeout=10000
function Read-For([int]$Ms) {
    $deadline=[DateTime]::UtcNow.AddMilliseconds($Ms)
    $text=''
    while ([DateTime]::UtcNow -lt $deadline) {
        $text+=$port.ReadExisting()
        Start-Sleep -Milliseconds 20
    }
    return $text
}
$echoDisabled=$false
try {
    $port.Open()
    $port.Write("`r")
    $prompt=Read-For 1000
    if ($prompt -notmatch 'root@[^\r\n]+[#$]') { throw 'Root shell not ready; use serial_command.ps1 first' }
    $py="import sys,subprocess,base64,hashlib; state=subprocess.check_output(['stty','-g']).decode().strip(); subprocess.check_call(['stty','-echo','-icanon','min','1','time','0']); print('VOICE_UPLOAD_READY',flush=True); data=sys.stdin.buffer.read($($encoded.Length)); blob=base64.b64decode(data,validate=True); open('$RemotePath','wb').write(blob); subprocess.check_call(['stty',state]); print('VOICE_UPLOAD_SHA256='+hashlib.sha256(blob).hexdigest(),flush=True)"
    $shellPy="'"+$py.Replace("'", "'"+'"'+"'"+'"'+"'")+"'"
    $port.Write("python3 -c $shellPy`r")
    $echoDisabled=$true
    $ready=Read-For 1200
    if ($ready -notmatch 'VOICE_UPLOAD_READY[\r\n]') { throw 'Board upload receiver did not start' }
    $response=''
    for ($i=0; $i -lt $encoded.Length; $i+=1024) {
        $port.Write($encoded.Substring($i,[Math]::Min(1024,$encoded.Length-$i)))
        $response+=Read-For 110
    }
    $response+=Read-For 1500
    if ($response -notmatch [regex]::Escape($expected)) { throw "Upload checksum mismatch: $response" }
    $echoDisabled=$false
    if ($Executable) {
        $port.Write("chmod 755 $RemotePath`r")
        [void](Read-For 400)
    }
    Write-Output "UPLOAD_VERIFIED $RemotePath SHA256=$expected"
}
finally {
    if ($port.IsOpen) {
        if ($echoDisabled) {
            $port.Write([string][char]3)
            [void](Read-For 300)
            $port.Write("`rstty sane`r")
            [void](Read-For 200)
        }
        $port.Close()
    }
}
