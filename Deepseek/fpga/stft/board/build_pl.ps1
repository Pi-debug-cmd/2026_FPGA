# Cross-compile vc_stream_pl.cpp (PL STFT path) into the vc_o64_pl ARM binary.
# Self-contained for the competition package: sources are this directory's
# board/src plus host/app/{src,third_party} (WORLD + SoundTouch), read-only.
param(
  [string]$Out = "",
  [string]$Gxx = "D:\Vivado\SDK\2018.3\gnu\aarch32\nt\gcc-arm-linux-gnueabi\bin\arm-linux-gnueabihf-g++.exe"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)   # fpga\stft
if (-not $Out) { $Out = Join-Path $root "bitstream\vc_o64_pl" }
$pkg = Split-Path -Parent (Split-Path -Parent $root)                          # competition package root
$app = Join-Path $pkg "host\app"
if (-not (Test-Path $Gxx)) {
  $cmd = Get-Command arm-linux-gnueabihf-g++ -ErrorAction SilentlyContinue
  if (-not $cmd) { throw "cross g++ not found; pass -Gxx <path>" }
  $Gxx = $cmd.Source
}
foreach ($p in @("$app\src\st_cpu_stub.cpp", "$app\third_party\world", "$app\third_party\soundtouch")) {
  if (-not (Test-Path $p)) { throw "missing package source: $p" }
}

$world = Get-ChildItem "$app\third_party\world\*.cpp" | ForEach-Object { $_.FullName }
$st = Get-ChildItem "$app\third_party\soundtouch\*.cpp" | ForEach-Object { $_.FullName }
$src = @(
    (Join-Path $root "board\src\vc_stream_pl.cpp"),
    (Join-Path $root "board\src\pl_stft.cpp"),
    (Join-Path $app "src\st_cpu_stub.cpp")
) + $world + $st

$flags = @(
    "-O2", "-static", "-s", "-std=c++11", "-Wno-psabi",
    "-mcpu=cortex-a9", "-mfpu=neon", "-mfloat-abi=hard",
    "-I$app\third_party\world", "-I$app\third_party\soundtouch",
    "-I$app\src", "-I$root\board\src",
    "-DSOUNDTOUCH_DISABLE_X86_OPTIMIZATIONS",
    "-DVC_PL_DEFAULT=1",
    "-ffunction-sections", "-fdata-sections", "-pthread",
    "-o", $Out
)
$link = @("-static", "-s", "-Wl,--gc-sections", "-Wl,--whole-archive", "-lpthread",
          "-Wl,--no-whole-archive", "-lm", "-pthread")

$argv = $flags + $src + $link
Write-Host "[build] $Gxx ... ($($src.Count) sources)" -ForegroundColor Cyan
$sw = [Diagnostics.Stopwatch]::StartNew()
$ErrorActionPreference = 'Continue'
& $Gxx @argv 1> (Join-Path $root "report\build_pl.out.txt") 2> (Join-Path $root "report\build_pl.err.txt")
$ErrorActionPreference = 'Stop'
$rc = $LASTEXITCODE
$sw.Stop()
if ($rc -ne 0) { throw "compile failed rc=$rc (see report\build_pl.err.txt)" }
$f = Get-Item $Out
$sha = (Get-FileHash $f.FullName -Algorithm SHA256).Hash.ToLower()
Write-Host ("[ok] {0}  {1:N0} bytes  {2:N1} s  sha256={3}" -f $f.Name, $f.Length,
            $sw.Elapsed.TotalSeconds, $sha) -ForegroundColor Green
[pscustomobject]@{ path = $f.FullName; bytes = $f.Length; sha256 = $sha;
                   opts = "-O2 -static -s -DVC_PL_DEFAULT=1" } |
    ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $root "bitstream\vc_o64_pl.json")
