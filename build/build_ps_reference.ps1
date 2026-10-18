param(
    [string]$SdkRoot = 'D:/USER_Software/Xilinx_Vivado/SDK/2018.3'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$outputDirectory = Join-Path $projectRoot 'build/generated/ps_reference'
New-Item -ItemType Directory -Force $outputDirectory | Out-Null
$compiler = Join-Path $SdkRoot 'gnu/aarch32/nt/gcc-arm-linux-gnueabi/bin/arm-linux-gnueabihf-gcc.exe'
& $compiler -O2 -std=c99 -Wall -Wextra -Werror -march=armv7-a -mtune=cortex-a9 -mfpu=neon -mfloat-abi=hard (Join-Path $projectRoot 'src/ps/pitch_fixed.c') -o (Join-Path $outputDirectory 'pitch_fixed')
if ($LASTEXITCODE -ne 0) { throw 'ARM compilation failed' }
Get-FileHash -LiteralPath (Join-Path $outputDirectory 'pitch_fixed') -Algorithm SHA256
