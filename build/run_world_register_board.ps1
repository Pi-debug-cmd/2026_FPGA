# Run the target-registration tool on the board: upload -> gunzip -> positive/negative inputs -> fetch profiles.
# File I/O only: no ALSA, no playback, no recording. Every upload is SHA-verified.
param(
    [string]$PortName = 'COM14',
    [string]$RemoteDir = '/tmp/codex_reg_20261016'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path $root 'build/generated/world_register_20261016'
$report = Join-Path $root 'report'
$py = 'C:/Users/World/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'

# 1) gzip the payloads (mtime=0 so the archive is reproducible)
$files = @(
    @{ local = "$out/world_register_arm"; remote = 'world_register_arm.gz' },
    @{ local = "$out/inputs/target_t8_10s.wav"; remote = 'target_t8_10s.wav.gz' },
    @{ local = "$out/inputs/target_t5_8_20s.wav"; remote = 'target_t5_8_20s.wav.gz' },
    @{ local = "$out/inputs/reject_too_short.wav"; remote = 'reject_too_short.wav.gz' },
    @{ local = "$out/inputs/reject_silent.wav"; remote = 'reject_silent.wav.gz' }
)
$listFile = Join-Path $out 'upload_inputs.json'
$files | ConvertTo-Json -Compress | Set-Content -LiteralPath $listFile -Encoding ASCII
& $py -c @"
import gzip, hashlib, json, pathlib
items = json.loads(pathlib.Path(r'$listFile').read_text(encoding='utf-8'))
records = []
for item in items:
    src = pathlib.Path(item['local']); dst = pathlib.Path(str(src) + '.gz')
    raw = src.read_bytes()
    dst.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
    records.append({'local': src.name, 'gz': dst.name, 'raw_bytes': len(raw),
                    'gz_bytes': dst.stat().st_size,
                    'raw_sha256': hashlib.sha256(raw).hexdigest(),
                    'gz_sha256': hashlib.sha256(dst.read_bytes()).hexdigest()})
pathlib.Path(r'$out/upload_manifest.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
print('prepared', len(records), 'files')
"@
if ($LASTEXITCODE -ne 0) { throw 'gzip preparation failed' }

# 2) upload each payload
foreach ($item in $files) {
    $gz = "$($item.local).gz"
    $remote = "$RemoteDir/$($item.remote)"
    Write-Output "UPLOAD $($item.remote)"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'board/upload_file.ps1') `
        -LocalFile $gz -RemotePath $remote -PortName $PortName
    if ($LASTEXITCODE -ne 0) { throw "upload failed: $($item.remote)" }
}

# 3) gunzip and run on the board
$command = "mkdir -p $RemoteDir; cd $RemoteDir; " +
           "gzip -df world_register_arm.gz target_t8_10s.wav.gz target_t5_8_20s.wav.gz " +
           "reject_too_short.wav.gz reject_silent.wav.gz; chmod +x world_register_arm; " +
           "./world_register_arm target_t8_10s.wav p_t8.txt; echo RC_T8=`$?; " +
           "./world_register_arm target_t5_8_20s.wav p_t5_8.txt; echo RC_T5=`$?; " +
           "./world_register_arm reject_too_short.wav r_short.txt; echo RC_SHORT=`$?; " +
           "./world_register_arm reject_silent.wav r_silent.txt; echo RC_SILENT=`$?; " +
           "sha256sum p_t8.txt p_t5_8.txt target_t8_10s.wav target_t5_8_20s.wav"
Write-Output 'BOARD RUN'
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'board/serial_run.ps1') `
    -PortName $PortName -TimeoutSeconds 300 -BootWaitSeconds 25 `
    -LogPath (Join-Path $report 'world_register_board_20261016.log') -Command $command
if ($LASTEXITCODE -ne 0) { throw 'board run failed' }

# 4) fetch the two positive profiles
foreach ($name in 'p_t8.txt', 'p_t5_8.txt') {
    Write-Output "DOWNLOAD $name"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'board/download_file.ps1') `
        -RemotePath "$RemoteDir/$name" -LocalPath "$out/arm_$name" -PortName $PortName
    if ($LASTEXITCODE -ne 0) { throw "download failed: $name" }
}
Write-Output 'DONE'
