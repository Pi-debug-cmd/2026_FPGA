# download_board.ps1 - pull a /tmp file from the board as base64 over COM8.
#   .\download_board.ps1 -RemotePath /tmp/vc/y16pl.gz -LocalFile out.gz
param(
    [Parameter(Mandatory = $true)][string]$RemotePath,
    [Parameter(Mandatory = $true)][string]$LocalFile,
    [string]$PortName = 'COM8',
    [int]$TimeoutSec = 600
)
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $dir 'serial_lib.ps1')
if ($RemotePath -notmatch '^/tmp/[A-Za-z0-9._/-]+$') { throw "refusing remote path '$RemotePath'" }

$p = Connect-Board -PortName $PortName
try {
    $marker = '__DL' + (Get-Random -Minimum 100000 -Maximum 999999) + '__'
    $p.Write("base64 -w 76 '$RemotePath'`r")
    Start-Sleep -Milliseconds 150
    $p.Write("echo $marker`r")
    $sb = [System.Text.StringBuilder]::new()
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSec)
    $found = $false
    while ([DateTime]::UtcNow -lt $deadline) {
        $chunk = $p.ReadExisting()
        if ($chunk.Length -gt 0) {
            [void]$sb.Append($chunk)
            if ($sb.ToString().Contains($marker)) { $found = $true; break }
        } else {
            Start-Sleep -Milliseconds 20
        }
    }
    if (-not $found) { throw "timeout waiting for $marker" }
    $all = $sb.ToString()
    $idx = $all.IndexOf($marker)
    $b64 = $all.Substring(0, $idx)
    # drop the echoed command line and any prompt noise
    $lines = $b64 -split "`r?`n" | Where-Object { $_ -match '^[A-Za-z0-9+/=]+$' -and $_.Length -ge 4 }
    $clean = ($lines -join '')
    $bytes = [Convert]::FromBase64String($clean)
    [System.IO.File]::WriteAllBytes($LocalFile, $bytes)
    Write-Host ("downloaded {0} bytes -> {1}" -f $bytes.Length, $LocalFile)
} finally {
    Close-Board $p
}
