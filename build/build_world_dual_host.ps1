param([string]$Compiler = 'D:/mingw64/bin/g++.exe', [ValidateSet('world_dual_probe', 'world_live_stream')][string]$SourceName = 'world_dual_probe', [string]$BinaryName = '', [switch]$OptimizedAperiodicity)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$upstream = Join-Path $root 'build/generated/world_source_v035/pyworld-0.3.5/lib/World'
$out = Join-Path $root 'build/generated/world_budget'
$flags = @('-O3', '-std=c++11', '-ffp-contract=off', '-pthread')
$binary = if ($SourceName -eq 'world_dual_probe') { 'world_dual_native_v11' } else { 'world_live_native_v12' }
if ($BinaryName) {
    if ($BinaryName -notmatch '^world_[a-z_]+_v[0-9]+$') { throw 'Use a versioned host binary name' }
    $binary = $BinaryName
}
& $Compiler @flags -Wall -Wextra -Werror -I "$upstream/src" -I "$upstream/tools" -c "$root/src/ps/$SourceName.cpp" -o "$out/$binary.o"
if ($LASTEXITCODE -ne 0) { throw 'Host probe compilation failed' }
# Third-party WORLD is compiled with its existing warning policy.
$sources = @(Get-ChildItem -LiteralPath "$upstream/src" -Filter '*.cpp' | Where-Object Name -ne 'synthesisrealtime.cpp' | ForEach-Object FullName)
if ($OptimizedAperiodicity) {
    $apSource = "$out/optimized_aperiodicity/d4c.cpp"
    if (-not (Test-Path -LiteralPath $apSource)) { throw 'Run prepare_world_aperiodicity_optimization.py first' }
    $sources = @($sources | Where-Object { [IO.Path]::GetFileName($_) -ne 'd4c.cpp' }) + @($apSource)
}
& $Compiler @flags -I "$upstream/src" -I "$upstream/tools" "$out/$binary.o" @sources "$out/aligned_world_full/synthesisrealtime.cpp" "$upstream/tools/audioio.cpp" -lm -o "$out/$binary.exe"
if ($LASTEXITCODE -ne 0) { throw 'Host WORLD link failed' }
Get-FileHash -LiteralPath "$out/$binary.exe" -Algorithm SHA256
