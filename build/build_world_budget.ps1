param([string]$SdkRoot = 'D:/USER_Software/Xilinx_Vivado/SDK/2018.3', [string]$BinaryName = 'world_budget_v3', [switch]$OptimizedPhase, [switch]$AlignedStreamDC, [switch]$AlignedStreamFull, [switch]$OptimizedAperiodicity,
      [ValidateSet('world_budget.cpp', 'world_sliding_probe.cpp', 'world_dual_probe.cpp', 'world_live_stream.cpp')][string]$SourceFile = 'world_budget.cpp')
$ErrorActionPreference = 'Stop'
if ($BinaryName -notmatch '^world_budget_v[0-9]+$') { throw 'Use a versioned budget binary name' }
if ($AlignedStreamDC -and $AlignedStreamFull) { throw 'Select one stream alignment experiment' }
$projectRoot = Split-Path -Parent $PSScriptRoot
$upstream = Join-Path $projectRoot 'build/generated/world_source_v035/pyworld-0.3.5/lib/World'
$out = Join-Path $projectRoot 'build/generated/world_budget'
New-Item -ItemType Directory -Force $out | Out-Null
$compiler = Join-Path $SdkRoot 'gnu/aarch32/nt/gcc-arm-linux-gnueabi/bin/arm-linux-gnueabihf-g++.exe'
$flags = @('-O3', '-std=c++11', '-march=armv7-a', '-mtune=cortex-a9', '-mfpu=neon', '-mfloat-abi=hard', '-ffp-contract=off', '-pthread')
$ErrorActionPreference = 'Continue' # Windows PowerShell treats compiler stderr notes as errors.
& $compiler @flags -Wall -Wextra -Werror -I "$upstream/src" -I "$upstream/tools" -c "$projectRoot/src/ps/$SourceFile" -o "$out/$BinaryName.o"
$compileExit = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($compileExit -ne 0) { throw 'Budget probe compilation failed' }
$sources = @(Get-ChildItem -LiteralPath "$upstream/src" -Filter '*.cpp' | ForEach-Object FullName)
if ($OptimizedPhase) {
    $phaseSource = Join-Path $out 'optimized_world/synthesis.cpp'
    if (-not (Test-Path -LiteralPath $phaseSource)) { throw 'Run prepare_world_phase_optimization.py first' }
    $sources = @($sources | Where-Object { [IO.Path]::GetFileName($_) -ne 'synthesis.cpp' }) + @($phaseSource)
}
if ($AlignedStreamDC) {
    $streamSource = Join-Path $out 'aligned_world/synthesisrealtime.cpp'
    if (-not (Test-Path -LiteralPath $streamSource)) { throw 'Run prepare_world_stream_alignment.py first' }
    $sources = @($sources | Where-Object { [IO.Path]::GetFileName($_) -ne 'synthesisrealtime.cpp' }) + @($streamSource)
}
if ($AlignedStreamFull) {
    $streamSource = Join-Path $out 'aligned_world_full/synthesisrealtime.cpp'
    if (-not (Test-Path -LiteralPath $streamSource)) { throw 'Run prepare_world_stream_alignment.py --full first' }
    $sources = @($sources | Where-Object { [IO.Path]::GetFileName($_) -ne 'synthesisrealtime.cpp' }) + @($streamSource)
}
if ($OptimizedAperiodicity) {
    $apSource = Join-Path $out 'optimized_aperiodicity/d4c.cpp'
    if (-not (Test-Path -LiteralPath $apSource)) { throw 'Run prepare_world_aperiodicity_optimization.py first' }
    $sources = @($sources | Where-Object { [IO.Path]::GetFileName($_) -ne 'd4c.cpp' }) + @($apSource)
}
$ErrorActionPreference = 'Continue'
& $compiler @flags -static -I "$upstream/src" -I "$upstream/tools" "$out/$BinaryName.o" @sources "$upstream/tools/audioio.cpp" -lm -lrt -o "$out/$BinaryName"
$compileExit = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($compileExit -ne 0) { throw 'WORLD ARM build failed' }
Copy-Item -LiteralPath "$upstream/LICENSE.txt" -Destination "$out/WORLD_LICENSE.txt"
Copy-Item -LiteralPath "$projectRoot/build/generated/world_source_v035/source_manifest.json" -Destination "$out/source_manifest.json"
Get-FileHash -LiteralPath "$out/$BinaryName" -Algorithm SHA256
