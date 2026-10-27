# serial_lib.ps1 - robust COM8 console helper for Zynq-7020 bring-up (host side)
# dot-source this file, then: $p = Connect-Board; Invoke-BoardCmd $p 'uname -a'
# Connect-Board disables tty echo (so bulk transfers never flood the RX path);
# Close-Board restores echo. Output text is returned with ANSI escapes stripped.
$ErrorActionPreference = 'Stop'

function Strip-Ansi {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    $t = [regex]::Replace($Text, "\x1B\[[0-9;?]*[A-Za-z]", '')
    $t = [regex]::Replace($t, "\x1B\][^\x07]*\x07", '')
    return $t
}

function Connect-Board {
    param(
        [string]$PortName = 'COM8',
        [int]$BaudRate = 115200,
        [int]$LoginTimeoutSec = 15
    )
    $p = [System.IO.Ports.SerialPort]::new($PortName, $BaudRate,
            [System.IO.Ports.Parity]::None, 8, [System.IO.Ports.StopBits]::One)
    $p.Handshake = [System.IO.Ports.Handshake]::None
    $p.DtrEnable = $false
    $p.RtsEnable = $false
    $p.ReadTimeout = 200
    $p.WriteTimeout = 15000
    $p.Encoding = [System.Text.Encoding]::ASCII
    $p.Open()
    $p.DiscardInBuffer()
    $p.Write("`r")
    $buf = ''
    $deadline = [DateTime]::UtcNow.AddSeconds($LoginTimeoutSec)
    $loggedIn = $false
    while ([DateTime]::UtcNow -lt $deadline) {
        $buf += $p.ReadExisting()
        if ($buf.Length -gt 3000) { $buf = $buf.Substring($buf.Length - 3000) }
        if ($buf -match 'login:\s*$') { $p.Write("root`r"); Start-Sleep -Milliseconds 400; $buf = ''; continue }
        if ($buf -match 'Password:\s*$') { $p.Write("root`r"); Start-Sleep -Milliseconds 400; $buf = ''; continue }
        if ($buf -match '(?m)[#\$]\s*$') { $loggedIn = $true; break }
        Start-Sleep -Milliseconds 100
    }
    if (-not $loggedIn) {
        $tail = $buf.Substring([Math]::Max(0, $buf.Length - 300))
        $p.Close()
        throw "no root shell prompt on $PortName within $LoginTimeoutSec s; tail: $tail"
    }
    # Quiet the console while we drive it: no tty echo and a short prompt.
    # Only shell-session variables are touched; /etc/profile is never modified.
    $setup = 'stty -echo; OLD_PS1="$PS1"; export PS1="br# "'
    $p.Write($setup + "`r")
    Start-Sleep -Milliseconds 400
    [void]$p.ReadExisting()
    return $p
}

function Read-Until {
    param($Port, [string]$Pattern, [int]$TimeoutSec = 20, [System.Text.StringBuilder]$Sink)
    $buf = ''
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSec)
    while ([DateTime]::UtcNow -lt $deadline) {
        $part = $Port.ReadExisting()
        if ($part.Length -gt 0) {
            $buf += $part
            if ($Sink) { [void]$Sink.Append($part) }
            $m = [regex]::Match($buf, $Pattern)
            if ($m.Success) { return @{ Match = $m; Buffer = $buf } }
        } else {
            Start-Sleep -Milliseconds 30
        }
    }
    return @{ Match = $null; Buffer = $buf }
}

# Runs a command, waits for the __XD marker, returns @{ Ok; ExitCode; Output; Raw }
function Invoke-BoardCmd {
    param($Port, [string]$Command, [int]$TimeoutSec = 20, [switch]$Quiet)
    $marker = '__XD' + (Get-Random -Minimum 100000 -Maximum 999999) + '__'
    $Port.Write($Command + "`r")
    Start-Sleep -Milliseconds 80
    $Port.Write("echo $marker=`$?`r")
    $r = Read-Until -Port $Port -Pattern ($marker + '=(\d+)') -TimeoutSec $TimeoutSec
    $stamp = Get-Date -Format 'HH:mm:ss'
    if (-not $r.Match) {
        $clean = Strip-Ansi $r.Buffer
        if (-not $Quiet) {
            Write-Host "[$stamp] TIMEOUT after ${TimeoutSec}s: $Command" -ForegroundColor Yellow
            Write-Host $clean
        }
        return @{ Ok = $false; ExitCode = 124; Output = $clean; Raw = $r.Buffer }
    }
    $code = [int]$r.Match.Groups[1].Value
    $raw = $r.Buffer
    $idx = $raw.IndexOf($r.Match.Value)
    $body = if ($idx -ge 0) { $raw.Substring(0, $idx) } else { $raw }
    $clean = Strip-Ansi $body
    # with echo off the body already starts with the command's own output; drop a
    # leading echoed prompt fragment if one leaked through
    $lines = $clean -split "`r?`n"
    if ($lines.Count -gt 1 -and $lines[0].Trim() -eq '') { $lines = $lines[1..($lines.Count - 1)] }
    $clean = ($lines -join "`n").TrimEnd()
    if (-not $Quiet) {
        Write-Host "[$stamp] $ $Command   -> exit=$code"
        if ($clean.Length -gt 0) { Write-Host $clean }
    }
    return @{ Ok = ($code -eq 0); ExitCode = $code; Output = $clean; Raw = $raw }
}

function Close-Board {
    param($Port)
    if ($Port -and $Port.IsOpen) {
        try {
            $restore = 'export PS1="$OLD_PS1"; unset OLD_PS1; stty echo'
            $Port.Write($restore + "`r")
            Start-Sleep -Milliseconds 300
        } catch { }
        try { $Port.Close() } catch { }
    }
}
