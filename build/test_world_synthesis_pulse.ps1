param(
    [string]$Compiler = 'D:/mingw64/bin/g++.exe'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path $root 'build/generated/world_synthesis_pulse_host'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$exe = Join-Path $out 'tb_world_synthesis_pulse.exe'
& $Compiler -std=c++11 -O2 `
    (Join-Path $root 'src/hls/world_synthesis_pulse.cpp') `
    (Join-Path $root 'sim/tb_world_synthesis_pulse.cpp') `
    -o $exe
if ($LASTEXITCODE -ne 0) { throw "compile failed: $LASTEXITCODE" }
& $exe
if ($LASTEXITCODE -ne 0) { throw "test failed: $LASTEXITCODE" }
