# stage.ps1 - assemble the working layout that the (unmodified) board scripts expect.
#
# The board tooling was written and verified against this layout:
#
#   <root>\tools\*.ps1      the scripts themselves
#   <root>\build\           vc_stream_arm
#   <root>\data\            student_v5.blob, test_src_32k_s24.raw
#   <root>\logs\            preflight/upload/run/download logs
#
# This script recreates it from the competition package without editing a single
# line of the verified scripts (their SHA-256 can therefore be checked against the
# originals).  Nothing is written inside the package.
#
#   .\stage.ps1                       # -> D:\vc_stage_20261026
#   .\stage.ps1 -Stage D:\stage_try
param(
    [string]$Stage = 'D:\vc_stage_20261026',
    [string]$Package = (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)))
)
$ErrorActionPreference = 'Stop'

$dst = @{
    tools = Join-Path $Stage 'tools'
    bin   = Join-Path $Stage 'tools\bin'
    build = Join-Path $Stage 'build'
    data  = Join-Path $Stage 'data'
    logs  = Join-Path $Stage 'logs'
}
foreach ($d in $dst.Values) { New-Item -ItemType Directory -Force -Path $d | Out-Null }

# 1) scripts (verbatim)
Copy-Item (Join-Path $Package 'host\deploy\*.ps1') $dst.tools -Force
Copy-Item (Join-Path $Package 'host\deploy\*.py')  $dst.tools -Force
Copy-Item (Join-Path $Package 'host\deploy\bin\*') $dst.bin -Force
Remove-Item (Join-Path $dst.tools 'stage.ps1') -ErrorAction SilentlyContinue
Remove-Item (Join-Path $dst.tools 'deploy_all.ps1') -ErrorAction SilentlyContinue

# 2) board executable: build it if missing, otherwise reuse a prebuilt one
$exe = Join-Path $dst.build 'vc_stream_arm'
if (Test-Path (Join-Path $Package 'host\app\build\vc_stream_arm')) {
    Copy-Item (Join-Path $Package 'host\app\build\vc_stream_arm') $exe -Force
} else {
    Write-Host "[stage] no prebuilt vc_stream_arm; run host\app\build_arm.ps1 first" -ForegroundColor Yellow
}

# 3) model + test input
Copy-Item (Join-Path $Package 'host\model\student_v5.blob') $dst.data -Force
Copy-Item (Join-Path $Package 'metrics\inputs\test_src_32k_s24.raw') $dst.data -Force

# 4) PL assets used by the overlay skill
Copy-Item (Join-Path $Package 'fpga\build\audio_pitch_dma_2018_swap.bin') $dst.bin -Force
Copy-Item (Join-Path $Package 'fpga\build\audio_pitch_dma_2018_swap.bin.gz') $dst.bin -Force
Copy-Item (Join-Path $Package 'skill\overlay_load_and_verify\overlay.py') $dst.tools -Force
Copy-Item (Join-Path $Package 'skill\overlay_load_and_verify\regtool.py') $dst.tools -Force
Copy-Item (Join-Path $Package 'skill\overlay_load_and_verify\bin\regtool') $dst.bin -Force
Copy-Item (Join-Path $Package 'skill\overlay_load_and_verify\example\register_map.json') `
          (Join-Path $dst.tools 'regmap.json') -Force
Copy-Item (Join-Path $Package 'skill\overlay_load_and_verify\example\consumers.txt') `
          (Join-Path $dst.tools 'consumers.txt') -Force
Copy-Item (Join-Path $Package 'skill\dma_cache_coherency\bin\dma_roundtrip') $dst.bin -Force

Write-Host "[stage] layout ready at $Stage" -ForegroundColor Green
Write-Host "        tools: $($dst.tools)"
Write-Host "        bin  : $($dst.bin)"
Write-Host "        build: $($dst.build)"
Write-Host "        data : $($dst.data)"
Get-ChildItem $dst.tools, $dst.bin, $dst.build, $dst.data -File |
    Select-Object Directory, Name, Length | Format-Table -AutoSize
