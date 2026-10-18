param(
    [string]$VivadoRoot = 'D:/USER_Software/Xilinx_Vivado/Vivado/2018.3'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$outputDirectory = Join-Path $projectRoot 'build/generated/axis_bypass_sim'
New-Item -ItemType Directory -Force $outputDirectory | Out-Null
Push-Location $outputDirectory
try {
    & (Join-Path $VivadoRoot 'bin/xvlog.bat') (Join-Path $projectRoot 'src/rtl/axis_audio_bypass.v') (Join-Path $projectRoot 'sim/tb_axis_audio_bypass.v')
    if ($LASTEXITCODE -ne 0) { throw 'xvlog failed' }
    & (Join-Path $VivadoRoot 'bin/xelab.bat') tb_axis_audio_bypass -s bypass_test
    if ($LASTEXITCODE -ne 0) { throw 'xelab failed' }
    & (Join-Path $VivadoRoot 'bin/xsim.bat') bypass_test -runall -log xsim.log
    if ($LASTEXITCODE -ne 0) { throw 'xsim failed' }
    if (!(Select-String -LiteralPath (Join-Path $outputDirectory 'xsim.log') -Pattern '^PASS:' -Quiet)) {
        throw 'Simulation did not reach the PASS marker'
    }
    Copy-Item -LiteralPath (Join-Path $outputDirectory 'xsim.log') -Destination (Join-Path $projectRoot 'report/axis_bypass_sim.txt')
} finally {
    Pop-Location
}
