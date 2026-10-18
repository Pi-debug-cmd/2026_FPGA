param(
    [string]$VivadoRoot = 'D:/USER_Software/Xilinx_Vivado/Vivado/2018.3',
    [string]$PythonExe = 'C:/Users/World/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$outputDirectory = Join-Path $projectRoot 'build/generated/pitch_sim'
New-Item -ItemType Directory -Force $outputDirectory | Out-Null
Push-Location $projectRoot
try {
    & $PythonExe -m sim.generate_pitch_vectors $outputDirectory
    if ($LASTEXITCODE -ne 0) { throw 'Vector generation failed' }
} finally { Pop-Location }
Push-Location $outputDirectory
try {
    & (Join-Path $VivadoRoot 'bin/xvlog.bat') -sv (Join-Path $projectRoot 'src/rtl/pcm_delay_ram.v') (Join-Path $projectRoot 'src/rtl/axis_pitch_shift.v') (Join-Path $projectRoot 'sim/tb_axis_pitch_shift.v')
    if ($LASTEXITCODE -ne 0) { throw 'xvlog failed' }
    & (Join-Path $VivadoRoot 'bin/xelab.bat') tb_axis_pitch_shift -s pitch_test
    if ($LASTEXITCODE -ne 0) { throw 'xelab failed' }
    & (Join-Path $VivadoRoot 'bin/xsim.bat') pitch_test -runall -log xsim.log
    if ($LASTEXITCODE -ne 0) { throw 'xsim failed' }
    if (!(Select-String -LiteralPath (Join-Path $outputDirectory 'xsim.log') -Pattern '^PASS:' -Quiet)) {
        throw 'Simulation did not reach the PASS marker'
    }
    Copy-Item -LiteralPath (Join-Path $outputDirectory 'xsim.log') -Destination (Join-Path $projectRoot 'report/pitch_sim.txt')
} finally { Pop-Location }
