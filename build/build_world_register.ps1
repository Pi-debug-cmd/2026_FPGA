param([string]$SdkRoot = 'D:/USER_Software/Xilinx_Vivado/SDK/2018.3')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$upstream = Join-Path $root 'build/generated/world_source_v035/pyworld-0.3.5/lib/World'
$out = Join-Path $root 'build/generated/world_register_20261016'
New-Item -ItemType Directory -Force $out | Out-Null
$sources = @(Get-ChildItem -LiteralPath "$upstream/src" -Filter '*.cpp' | ForEach-Object FullName)
$audioio = "$upstream/tools/audioio.cpp"
$tools = @('world_register', 'world_convert')
$hostFlags = @('-O3', '-std=c++11', '-ffp-contract=off', '-pthread', '-Wall', '-Wextra',
               '-I', "$upstream/src", '-I', "$upstream/tools")
$compiler = Join-Path $SdkRoot 'gnu/aarch32/nt/gcc-arm-linux-gnueabi/bin/arm-linux-gnueabihf-g++.exe'
if (-not (Test-Path -LiteralPath $compiler)) { throw 'SDK ARM compiler is missing' }
$armFlags = @('-O3', '-std=c++11', '-march=armv7-a', '-mtune=cortex-a9', '-mfpu=neon',
              '-mfloat-abi=hard', '-ffp-contract=off', '-pthread', '-static',
              '-ffunction-sections', '-fdata-sections', '-Wl,--gc-sections',
              '-Wall', '-Wextra', '-I', "$upstream/src", '-I', "$upstream/tools")

foreach ($tool in $tools) {
    $source = "$root/src/ps/$tool.cpp"
    if (-not (Test-Path -LiteralPath $source)) { throw "missing source: $tool" }
    Write-Output "--- host $tool ---"
    $ErrorActionPreference = 'Continue'
    & 'D:/mingw64/bin/g++.exe' @hostFlags $source @sources $audioio -lm -o "$out/${tool}_host.exe"
    $hostExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($hostExit -ne 0) { throw "host build failed: $tool" }
    Write-Output ('host  ' + (Get-FileHash -LiteralPath "$out/${tool}_host.exe" -Algorithm SHA256).Hash)

    Write-Output "--- arm $tool ---"
    $ErrorActionPreference = 'Continue'
    & $compiler @armFlags $source @sources $audioio -lm -lrt -o "$out/${tool}_arm"
    $armExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($armExit -ne 0 -or -not (Test-Path -LiteralPath "$out/${tool}_arm")) { throw "ARM build failed: $tool" }
    Write-Output ('arm   ' + (Get-FileHash -LiteralPath "$out/${tool}_arm" -Algorithm SHA256).Hash)
}
Copy-Item -LiteralPath "$upstream/LICENSE.txt" -Destination "$out/WORLD_LICENSE.txt" -Force
Write-Output 'BUILD OK'
