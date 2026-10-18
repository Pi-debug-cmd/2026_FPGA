# Closed loop on the board: target profile + source WAV + world_convert -> converted WAV.
# File I/O only: no ALSA, no playback, no recording. Every transfer is SHA-verified.
param(
    [string]$PortName = 'COM14',
    [string]$RemoteDir = '/tmp/codex_convert_20261017'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path $root 'build/generated/world_register_20261016'
$report = Join-Path $root 'report'
$py = 'C:/Users/World/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'

Copy-Item -LiteralPath (Join-Path $out 'profile_t5_8.txt') -Destination (Join-Path $out 'profile.txt') -Force
$files = @(
    @{ local = "$out/world_convert_arm"; remote = 'world_convert_arm.gz' },
    @{ local = "$out/profile.txt"; remote = 'profile.txt.gz' },
    @{ local = "$out/inputs/source_holdout.wav"; remote = 'source_holdout.wav.gz' }
)
$listFile = Join-Path $out 'convert_upload_inputs.json'
$files | ConvertTo-Json -Compress | Set-Content -LiteralPath $listFile -Encoding ASCII
& $py -c @"
import gzip, hashlib, json, pathlib
items = json.loads(pathlib.Path(r'$listFile').read_text(encoding='utf-8'))
records = []
for item in items:
    src = pathlib.Path(item['local']); dst = pathlib.Path(str(src) + '.gz')
    raw = src.read_bytes()
    dst.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
    records.append({'local': src.name, 'raw_bytes': len(raw), 'gz_bytes': dst.stat().st_size,
                    'raw_sha256': hashlib.sha256(raw).hexdigest(),
                    'gz_sha256': hashlib.sha256(dst.read_bytes()).hexdigest()})
pathlib.Path(r'$out/convert_upload_manifest.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
print('prepared', len(records))
"@
if ($LASTEXITCODE -ne 0) { throw 'gzip preparation failed' }

foreach ($item in $files) {
    Write-Output "UPLOAD $($item.remote)"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'board/upload_file.ps1') `
        -LocalFile "$($item.local).gz" -RemotePath "$RemoteDir/$($item.remote)" -PortName $PortName
    if ($LASTEXITCODE -ne 0) { throw "upload failed: $($item.remote)" }
}

$command = "mkdir -p $RemoteDir; cd $RemoteDir; " +
           "gzip -df world_convert_arm.gz profile.txt.gz source_holdout.wav.gz; " +
           "chmod +x world_convert_arm; " +
           "time ./world_convert_arm source_holdout.wav profile.txt closed_loop.wav; echo RC_CONVERT=`$?; " +
           "sha256sum closed_loop.wav"
Write-Output 'BOARD RUN'
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'board/serial_run.ps1') `
    -PortName $PortName -TimeoutSeconds 420 -BootWaitSeconds 25 `
    -LogPath (Join-Path $report 'world_convert_board_20261017.log') -Command $command
if ($LASTEXITCODE -ne 0) { throw 'board run failed' }

Write-Output 'DOWNLOAD closed_loop.wav'
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'board/download_file.ps1') `
    -RemotePath "$RemoteDir/closed_loop.wav" -LocalPath "$out/closed_loop_arm.wav" -PortName $PortName
if ($LASTEXITCODE -ne 0) { throw 'download failed' }
Write-Output 'DONE'
