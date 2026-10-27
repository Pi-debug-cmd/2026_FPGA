param(
  [Parameter(Mandatory=$true)][string]$WorldRoot,
  [ValidateSet('arm','host')][string]$Target='arm',
  [string]$Compiler='',
  [switch]$ProfileOperators
)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$out=Join-Path $root 'build/generated/world_exp_ps'
New-Item -ItemType Directory -Force $out | Out-Null
if (!$Compiler) {
  $Compiler=if($Target -eq 'arm') {'D:/USER_Software/vivado/2026.1/gnu/aarch32/nt/gcc-arm-linux-gnueabi/bin/arm-linux-gnueabihf-g++.exe'} else {'D:/mingw64/bin/g++.exe'}
}
# common.cpp is upstream, with one guarded early return at the exp loop.
$common=Get-Content -Raw "$WorldRoot/src/common.cpp"
if ((Get-FileHash "$WorldRoot/src/common.cpp").Hash -ne 'EF4A982D103BFD4C0EFE6F1E6FA1192809E07AC39289F29951F3D95F1AF8CA51') {throw 'Unexpected WORLD common.cpp'}
$common=$common.Replace('#include <math.h>', "#include <math.h>`n#include `"world_exp_hook.h`"")
$common=$common.Replace('  // Since x is complex number, calculation of exp(x) is as following.', "  if (WorldExpOffload(minimum_phase->minimum_phase_spectrum, minimum_phase->fft_size)) return;`n  // Since x is complex number, calculation of exp(x) is as following.")
[IO.File]::WriteAllText("$out/common.cpp",$common)
python "$root/build/gen_world_exp_tables.py" --out "$out/world_exp_tables.h"
if ($LASTEXITCODE) {throw 'Table generation failed'}
$sources=@(Get-ChildItem "$WorldRoot/src/*.cpp" | Where-Object Name -NotIn @('common.cpp','synthesis.cpp','synthesisrealtime.cpp') | ForEach-Object FullName)
$flags=@('-O3','-funroll-loops','-fno-math-errno','-fno-trapping-math','-std=c++11','-ffp-contract=off','-pthread','-static')
if($Target -eq 'arm') {$flags+=@('-mcpu=cortex-a9','-mfpu=neon','-mfloat-abi=hard')}
$includes=@('-I',"$root/src/ps/world_v23",'-I',"$root/src/ps",'-I',$out,'-I',"$WorldRoot/src",'-I',"$WorldRoot/tools")
$bin="$out/world_exp_$Target"
if($ProfileOperators) {
  $bin+='_profile'
  $sources+=@("$root/src/ps/world_operator_profile.cpp")
  foreach($symbol in @('fft_execute','fft_plan_dft_1d','fft_plan_dft_r2c_1d','fft_plan_dft_c2r_1d','Dio','StoneMask','CheapTrick','D4C')) {
    $flags+=('-Wl,--wrap='+$symbol)
  }
}
if($Target -eq 'host') {$bin+='.exe'}
& $Compiler @flags @includes "$root/src/ps/world_live_stream.cpp" "$root/src/ps/world_exp_hook.cpp" "$out/common.cpp" "$root/src/ps/world_v23/synthesis.cpp" "$root/src/ps/world_v23/synthesisrealtime.cpp" @sources "$WorldRoot/tools/audioio.cpp" -lm -o $bin
if($LASTEXITCODE) {throw 'WORLD exp build failed'}
if($Target -eq 'arm') {
  & $Compiler -O3 -std=c++11 -Wall -Wextra -Werror -static "$root/src/ps/world_exp_dma_probe.cpp" -o "$out/world_exp_dma_probe"
  if($LASTEXITCODE) {throw 'DMA probe build failed'}
}
Get-FileHash $bin
