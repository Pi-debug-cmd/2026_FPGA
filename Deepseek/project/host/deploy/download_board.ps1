# download_board.ps1 - pull a /tmp file back over COM8 (base64 over the console)
#
#   .\download_board.ps1 -RemotePath /tmp/bringup_1k_s24.wav -LocalPath .\bringup_1k_s24.wav
#
# The board side only runs `base64 <file>; echo __B64_END__`; nothing is written
# on the board (the console stream is captured directly). Host decodes and
# compares SHA-256 against a second remote `sha256sum`.
param(
    [Parameter(Mandatory = $true)][string]$RemotePath,
    [Parameter(Mandatory = $true)][string]$LocalPath,
    [string]$PortName = 'COM8'
)
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $dir 'serial_lib.ps1')
if ($RemotePath -notmatch '^/tmp/[A-Za-z0-9._/-]+$') { throw "only /tmp/<name> is allowed: $RemotePath" }

$p = Connect-Board -PortName $PortName
try {
    $q = Invoke-BoardCmd $p "wc -c < '$RemotePath'; sha256sum '$RemotePath'" -Quiet
    if ($q.ExitCode -ne 0) { throw "remote file missing: $RemotePath" }
    $remoteSize = [long]([regex]::Match($q.Output, '\d+')).Value
    $remoteSha = [regex]::Match($q.Output, '[0-9a-f]{64}').Value
    Write-Host "remote: $RemotePath  bytes=$remoteSize  sha256=$remoteSha"

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $p.Write("echo __B64_BEGIN__; base64 '$RemotePath'; echo; echo __B64_END__`n")
    $r = Read-Until -Port $p -Pattern '__B64_END__' -TimeoutSec 300
    $sw.Stop()
    if (-not $r.Match) { throw 'timed out waiting for base64 payload' }
    $endIdx = $r.Buffer.LastIndexOf('__B64_END__')
    $beginIdx = $r.Buffer.LastIndexOf('__B64_BEGIN__', $endIdx)
    if ($beginIdx -lt 0) { throw 'begin marker missing' }
    $body = $r.Buffer.Substring($beginIdx + '__B64_BEGIN__'.Length, $endIdx - $beginIdx - '__B64_BEGIN__'.Length)
    $b64 = (($body -split "`r?`n" | ForEach-Object { $_.Trim() }) | Where-Object { $_ -match '^[A-Za-z0-9+/=]+$' }) -join ''
    $bytes = [Convert]::FromBase64String($b64)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $localSha = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    $sha.Dispose()

    [System.IO.File]::WriteAllBytes($LocalPath, $bytes)
    $elapsed = $sw.Elapsed.TotalSeconds
    Write-Host ("downloaded {0} bytes, base64 {1} bytes, {2:N1} s, {3:N2} KB/s (base64), sha256={4}" -f `
        $bytes.Length, $b64.Length, $elapsed, ($b64.Length / 1024.0 / $elapsed), $localSha)
    if ($bytes.Length -ne $remoteSize -or $localSha -ne $remoteSha) {
        throw "download verification failed (size $($bytes.Length)/$remoteSize, sha $localSha/$remoteSha)"
    }
    Write-Host 'DOWNLOAD_VERIFIED'
} finally {
    Close-Board $p
}
