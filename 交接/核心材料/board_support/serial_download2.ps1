param(
    [Parameter(Mandatory=$true)][string]$RemotePath,
    [Parameter(Mandatory=$true)][string]$LocalPath,
    [string]$PortName='COM8',
    [int]$ChunkBytes=3072
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
    $py = "import sys,base64; data=open('$RemotePath','rb').read(); pos=0`nwhile True:`n line=sys.stdin.buffer.readline()`n if not line: break`n if line.strip()==b'NEXT':`n  chunk=data[pos:pos+$ChunkBytes]`n  if not chunk: sys.stdout.buffer.write(b'END\n'); sys.stdout.flush(); break`n  sys.stdout.buffer.write(base64.b64encode(chunk)+b'\n'); sys.stdout.flush(); pos+=$ChunkBytes"
    $shellPy="'"+$py.Replace("'", "'"+'"'+"'"+'"'+"'")+"'"
    $port.Write("stty -echo -icanon; python3 -c $shellPy; stty sane`r")
    Start-Sleep -Milliseconds 1200
    $port.ReadExisting() | Out-Null
    $all = New-Object System.IO.MemoryStream
    $chunks=0
    while ($true) {
        $port.Write("NEXT`n")
        $line=''; $deadline=[DateTime]::UtcNow.AddSeconds(15)
        while ([DateTime]::UtcNow -lt $deadline -and -not $line.EndsWith("`n")) {
            Start-Sleep -Milliseconds 20
            $line += $port.ReadExisting()
        }
        $line = $line.Trim()
        if ($line -eq 'END') { break }
        if ($line -notmatch '^[A-Za-z0-9+/=]+$') { throw "bad chunk: $line" }
        $all.Write([Convert]::FromBase64String($line),0,0) | Out-Null
        $bytes=[Convert]::FromBase64String($line)
        $all.Write($bytes,0,$bytes.Length)
        $chunks++
        if ($chunks % 10 -eq 0) { Write-Output ("chunks=$chunks bytes=" + $all.Length) }
    }
    $out = $all.ToArray()
    [IO.File]::WriteAllBytes($LocalPath,$out)
    Write-Output "DOWNLOAD_VERIFIED $RemotePath -> $LocalPath bytes=$($out.Length)"
}
finally {
    $port.Close()
}
