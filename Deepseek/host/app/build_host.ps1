# Desk-side (native x86-64 Windows) build of the exact same sources.
#
# Purpose: the ARM binary and this one run identical code, so numerical work
# (C vs Python stage by stage) can be done here in seconds instead of over the
# 10 KB/s serial link.  The shipped artefact is always build\vc_stream_arm.
#
#   .\build_host.ps1
#   .\build_host.ps1 -Cxx 'C:\msys64\mingw64\bin\g++.exe'   # any x86-64 g++ 7+ works
param(
    [string]$Cxx = $(if ($env:FVC_HOST_CXX) { $env:FVC_HOST_CXX }
                     else { "D:\Vivado\Vivado\2018.3\msys64\mingw64\bin\g++.exe" }),
    [string]$Out = "build\vc_stream_host.exe"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
if (-not (Test-Path $Cxx)) {
    throw ("host g++ not found: $Cxx`n" +
           "  pass -Cxx <path> or set `$env:FVC_HOST_CXX (any x86-64 mingw g++ 7+ works)")
}
# cc1plus is launched with its own path, so the mingw bin dir must be on PATH for
# the DLLs it needs (otherwise the compiler dies silently with rc=1).
$env:PATH = "$(Split-Path -Parent $Cxx);$env:PATH"

$src = @("src\vc_stream.cpp", "src\st_cpu_stub.cpp") +
       (Get-ChildItem "third_party\world\*.cpp" | ForEach-Object { $_.FullName }) +
       (Get-ChildItem "third_party\soundtouch\*.cpp" | ForEach-Object { $_.FullName })

$flags = @("-O2", "-std=c++11", "-Wno-psabi",
           "-Ithird_party/world", "-Ithird_party/soundtouch", "-DSOUNDTOUCH_DISABLE_X86_OPTIMIZATIONS",
           "-o", $Out, "-pthread") + $src + @("-lm", "-static")
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Out) | Out-Null
$log = "logs\build_host.log"
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
$argv = ($flags | ForEach-Object { if ($_ -match '\s') { "`"$_`"" } else { $_ } }) -join ' '
cmd /c "`"$Cxx`" $argv > `"$log`" 2>&1"
$rc = $LASTEXITCODE
if ($rc -ne 0) { Get-Content $log | Select-Object -Last 40; throw "host build failed rc=$rc" }
$f = Get-Item $Out
Write-Host ("[ok] host {0}  {1:N0} bytes  sha256={2}" -f $f.Name, $f.Length,
    (Get-FileHash $f.FullName -Algorithm SHA256).Hash.ToLower()) -ForegroundColor Green

