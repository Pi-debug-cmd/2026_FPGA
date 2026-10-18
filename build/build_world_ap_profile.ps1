param([string]$SdkRoot = 'D:/USER_Software/Xilinx_Vivado/SDK/2018.3')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$upstream = Join-Path $root 'build/generated/world_source_v035/pyworld-0.3.5/lib/World'
$out = Join-Path $root 'build/generated/world_budget'
$dependencies = @("$upstream/src/common.cpp", "$upstream/src/fft.cpp", "$upstream/src/matlabfunctions.cpp")
$hostFlags = @('-O3', '-std=c++11', '-ffp-contract=off', '-pthread', '-I', "$upstream/src")
& 'D:/mingw64/bin/g++.exe' @hostFlags "$root/sim/world_aperiodicity_profile.cpp" @dependencies -lm -o "$out/world_ap_profile_v1.exe"
if ($LASTEXITCODE -ne 0) { throw 'Host D4C internal benchmark build failed' }
$compiler = Join-Path $SdkRoot 'gnu/aarch32/nt/gcc-arm-linux-gnueabi/bin/arm-linux-gnueabihf-g++.exe'
if (-not (Test-Path -LiteralPath $compiler)) { throw 'SDK ARM compiler is missing' }
$armFlags = @('-O3', '-std=c++11', '-march=armv7-a', '-mtune=cortex-a9', '-mfpu=neon',
              '-mfloat-abi=hard', '-ffp-contract=off', '-pthread', '-static',
              '-ffunction-sections', '-fdata-sections', '-Wl,--gc-sections',
              '-I', "$upstream/src")
$ErrorActionPreference = 'Continue'
& $compiler @armFlags "$root/sim/world_aperiodicity_profile.cpp" @dependencies -lm -lrt -o "$out/world_ap_profile_v1"
$compileExit = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($compileExit -ne 0 -or -not (Test-Path -LiteralPath "$out/world_ap_profile_v1")) { throw 'ARM D4C internal benchmark build failed' }
Get-FileHash -LiteralPath "$out/world_ap_profile_v1" -Algorithm SHA256
