# Cross-compile vc_stream.cpp + WORLD + SoundTouch into one static ARM ELF and
# verify the artefact (ELF32/ARM/hard-float/EXEC, no INTERP segment).
#
#   .\build_arm.ps1                 # default -O2
#   .\build_arm.ps1 -ExtraFlags "-O3"  # experiment with optimisation
#   .\build_arm.ps1 -GccDir 'C:\Xilinx\SDK\2018.3\gnu\aarch32\nt\gcc-arm-linux-gnueabi\bin'
#   $env:FVC_GCC_DIR = '...'        # same, via environment (no absolute path baked in)
param(
    [string]$Out = "build\vc_stream_arm",
    [string]$ExtraFlags = "",
    [string]$GccDir = $env:FVC_GCC_DIR
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root
try {
    if (-not $GccDir) { $GccDir = "D:\Vivado\SDK\2018.3\gnu\aarch32\nt\gcc-arm-linux-gnueabi\bin" }
    $gxx = Join-Path $GccDir "arm-linux-gnueabihf-g++.exe"
    if (-not (Test-Path $gxx)) {
        throw ("cross g++ not found: $gxx`n" +
               "  pass -GccDir <dir> or set `$env:FVC_GCC_DIR to the SDK 2018.3 bin directory")
    }

    $world = Get-ChildItem "third_party\world\*.cpp" | ForEach-Object { $_.FullName }
    $st = Get-ChildItem "third_party\soundtouch\*.cpp" | ForEach-Object { $_.FullName }
    $src = @("src\vc_stream.cpp", "src\st_cpu_stub.cpp") + $world + $st

    $flags = @(
        "-O2", "-static", "-s", "-std=c++11",
        "-mcpu=cortex-a9", "-mfpu=neon", "-mfloat-abi=hard", "-Wno-psabi",
        "-Ithird_party/world", "-Ithird_party/soundtouch",
        "-ffunction-sections", "-fdata-sections", "-pthread",
        "-o", $Out
    )
    if ($ExtraFlags) { $flags = ($ExtraFlags -split ' ') + $flags }
    $link = @("-static", "-s", "-Wl,--gc-sections", "-Wl,--whole-archive", "-lpthread", "-Wl,--no-whole-archive", "-lm", "-pthread")

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Out) | Out-Null
    $argv = $flags + $src + $link
    Write-Host "[build] $gxx $($argv -join ' ')" -ForegroundColor Cyan
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & $gxx @argv
    $rc = $LASTEXITCODE
    $sw.Stop()
    if ($rc -ne 0) { throw "compile failed rc=$rc" }

    $f = Get-Item $Out
    Write-Host ""
    Write-Host ("[ok] {0}  {1:N0} bytes  built in {2:N1} s" -f $f.Name, $f.Length, $sw.Elapsed.TotalSeconds) -ForegroundColor Green

    # ---- artefact verification
    $bytes = [System.IO.File]::ReadAllBytes($f.FullName)
    function Hex($b, $n) { ($b[0..($n-1)] | ForEach-Object { $_.ToString("x2") }) -join " " }
    Write-Host ("magic    : " + (Hex $bytes 4))
    Write-Host ("e_machine: 0x{0:x2}{1:x2} (0x28 = ARM)" -f $bytes[19], $bytes[18])
    Write-Host ("e_type   : 0x{0:x2}{1:x2} (0x02 = EXEC)" -f $bytes[17], $bytes[16])
    Write-Host ("flags    : 0x{0:x2}{1:x2}{2:x2}{3:x2} (0x05000400 = EABI5 hard-float)" -f $bytes[39], $bytes[38], $bytes[37], $bytes[36])
    $sha = (Get-FileHash $f.FullName -Algorithm SHA256).Hash.ToLower()
    Write-Host ("sha256   : " + $sha)
    [pscustomobject]@{
        path = $f.FullName; bytes = $f.Length; sha256 = $sha
        opts = ("-O2 -static -s" + $(if ($ExtraFlags) { " " + $ExtraFlags } else { "" }))
    } | ConvertTo-Json | Set-Content -Encoding utf8 "build\vc_stream_arm.json"
}
finally { Pop-Location }
