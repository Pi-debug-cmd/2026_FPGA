# upload_board.ps1 - base64 chunked upload over COM8 with two-sided SHA-256
#
#   .\upload_board.ps1 -LocalFile .\bringup_tool -RemotePath /tmp/bringup_tool
#
# Protocol: tty echo is turned off; each chunk is a quoted heredoc appended to a
# .b64 file, then the remote tail of exactly that many bytes is hashed and
# compared with the host-side hash of the same text. A failed chunk is rolled
# back with truncate(1) and retried (chunk size is halved after 3 failures).
# Finally the remote decodes with base64 -d and both sides compare the SHA-256
# of the *binary*. Nothing outside /tmp/ is written.
param(
    [Parameter(Mandatory = $true)][string]$LocalFile,
    [Parameter(Mandatory = $true)][string]$RemotePath,
    [string]$PortName = 'COM8',
    [int]$LinesPerChunk = 320,     # 320 x 76 = 24320 base64 bytes per chunk
    [int]$MaxRetries = 3
)
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $dir 'serial_lib.ps1')

if ($RemotePath -notmatch '^/tmp/[A-Za-z0-9._/-]+$') { throw "refusing remote path '$RemotePath' (only /tmp/<name>)" }

$bytes = [System.IO.File]::ReadAllBytes($LocalFile)
$sha = [System.Security.Cryptography.SHA256]::Create()
$shaHost = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()

$b64 = [Convert]::ToBase64String($bytes)
$lines = [System.Collections.Generic.List[string]]::new()
for ($i = 0; $i -lt $b64.Length; $i += 76) {
    $lines.Add($b64.Substring($i, [Math]::Min(76, $b64.Length - $i)))
}

$p = Connect-Board -PortName $PortName

try {
    # never overwrite an existing board file: pick a fresh name if needed
    $probe = Invoke-BoardCmd $p "[ -e '$RemotePath' ] && echo EXISTS || echo MISSING" -Quiet
    if ($probe.Output -match 'EXISTS') {
        $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
        $RemotePath = "$RemotePath.$stamp"
        Write-Host "remote name already exists -> using $RemotePath"
    }
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $b64Path = "/tmp/" + (Split-Path -Leaf $RemotePath) + ".$stamp.b64"

    $r = Invoke-BoardCmd $p "rm -f '$b64Path'; echo READY" -Quiet
    if ($r.ExitCode -ne 0) { throw "cannot prepare $b64Path" }

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $offset = 0
    $chunkIdx = 0
    $retries = 0
    $linesPerChunk = $LinesPerChunk
    while ($offset -lt $lines.Count) {
        $take = [Math]::Min($linesPerChunk, $lines.Count - $offset)
        $text = (($lines.GetRange($offset, $take) | ForEach-Object { $_ }) -join "`n") + "`n"
        $chunkBytes = [System.Text.Encoding]::ASCII.GetByteCount($text)
        $chunkSha = ([BitConverter]::ToString($sha.ComputeHash([System.Text.Encoding]::ASCII.GetBytes($text)))).Replace('-', '').ToLowerInvariant()
        $prevLen = $script:remoteLen
        if ($null -eq $prevLen) { $prevLen = 0 }

        $ok = $false
        for ($attempt = 1; $attempt -le $MaxRetries -and -not $ok; $attempt++) {
            $p.Write("cat >> '$b64Path' <<'__BRUP_EOF__'`n")
            $p.Write($text)
            $p.Write("__BRUP_EOF__`n")
            $p.Write("echo __CHUNK_${chunkIdx}__=`$?`n")
            $ack = Read-Until -Port $p -Pattern "__CHUNK_${chunkIdx}__=(\d+)" -TimeoutSec 40
            if (-not $ack.Match) { Write-Host "chunk $chunkIdx attempt ${attempt}: no ack"; $retries++; continue }
            $got = Invoke-BoardCmd $p "tail -c $chunkBytes '$b64Path' | sha256sum" -Quiet
            $m = [regex]::Match($got.Output, '[0-9a-f]{64}')
            if (-not $m.Success -or $m.Value -ne $chunkSha) {
                Write-Host "chunk $chunkIdx attempt ${attempt}: sha mismatch, rolling back $prevLen"
                $retries++
                [void](Invoke-BoardCmd $p "truncate -s $prevLen '$b64Path'" -Quiet)
                continue
            }
            $ok = $true
        }
        if (-not $ok) {
            if ($linesPerChunk -le 40) { throw "chunk $chunkIdx failed after $MaxRetries attempts" }
            $linesPerChunk = [int]($linesPerChunk / 2)
            Write-Host "reducing chunk size to $linesPerChunk lines and restarting"
            [void](Invoke-BoardCmd $p "rm -f '$b64Path'" -Quiet)
            $offset = 0; $script:remoteLen = 0; $chunkIdx = 0
            continue
        }
        $script:remoteLen = $prevLen + $chunkBytes
        $offset += $take
        $chunkIdx++
        if (($chunkIdx % 10) -eq 0) {
            Write-Host ("progress {0}/{1} chunks  {2:N0}/{3:N0} base64 bytes  {4:N1} KB/s" -f `
                $chunkIdx, [Math]::Ceiling($lines.Count / $linesPerChunk), $script:remoteLen,
                [System.Text.Encoding]::ASCII.GetByteCount(($lines -join "`n") + "`n"), ($script:remoteLen / 1024.0 / $sw.Elapsed.TotalSeconds))
        }
    }
    $sw.Stop()
    $payloadBytes = [System.Text.Encoding]::ASCII.GetByteCount(($lines -join "`n") + "`n")

    # decode + verify binary on target
    $dec = Invoke-BoardCmd $p "base64 -d '$b64Path' > '$RemotePath' && chmod +x '$RemotePath' && sha256sum '$RemotePath'" -TimeoutSec 60 -Quiet
    $dm = [regex]::Match($dec.Output, '[0-9a-f]{64}')
    $shaRemote = if ($dm.Success) { $dm.Value } else { '<none>' }
    $sizeQ = Invoke-BoardCmd $p "wc -c < '$RemotePath'" -Quiet
    $sizeRemote = ([regex]::Match($sizeQ.Output, '\d+')).Value

    $result = [ordered]@{
        LocalFile    = $LocalFile
        RemotePath   = $RemotePath
        Bytes        = $bytes.Length
        Sha256Host   = $shaHost
        Sha256Remote = $shaRemote
        ShaMatch     = ($shaRemote -eq $shaHost)
        SizeRemote   = $sizeRemote
        ElapsedSec   = [Math]::Round($sw.Elapsed.TotalSeconds, 2)
        PayloadBytes = $payloadBytes
        RateKBps     = [Math]::Round($payloadBytes / 1024.0 / $sw.Elapsed.TotalSeconds, 2)
        BinRateKBps  = [Math]::Round($bytes.Length / 1024.0 / $sw.Elapsed.TotalSeconds, 2)
        Chunks       = $chunkIdx
        Retries      = $retries
        B64Path      = $b64Path
    }
    # drop our own scratch file only (never a pre-existing board file)
    [void](Invoke-BoardCmd $p "rm -f '$b64Path'" -Quiet)
} finally {
    Close-Board $p
    $sha.Dispose()
}

$result.GetEnumerator() | ForEach-Object { Write-Host ("{0,-13}: {1}" -f $_.Key, $_.Value) }
if (-not $result.ShaMatch) { throw "SHA-256 mismatch: host=$($result.Sha256Host) remote=$($result.Sha256Remote)" }
$result | ConvertTo-Json | Set-Content -Path (Join-Path $dir 'upload_result.json') -Encoding utf8
Write-Host "UPLOAD_VERIFIED"
