# build_pl.ps1 - rebuild the PL bitstream from the Tcl in ../src and verify the result.
#
# Steps (each is the same command that produced the shipped bitstream, see
# ../../fpga/report/build_changes_2018_3.md):
#   1. create_audio_pitch_dma.tcl   -> BD + wrapper + validate   (AUDIO_PITCH_DMA_VALIDATED)
#   2. synth_2018_3.tcl             -> synthesis                 (AUDIO_PITCH_DMA_SYNTHESIZED_2018_3)
#   3. impl_2018_3.tcl              -> place/route/bitstream     (AUDIO_PITCH_DMA_BITSTREAM_BUILT_2018_3)
#   4. export_hdf.tcl               -> .hdf + .hwdef             (HDF_EXPORTED)
#   5. make_swap.py                 -> fpga_manager image (+ .gz)
#   6. SHA-256 comparison against ../build/SHA256SUMS.txt
#
# NOTE: this script was assembled from the commands that were actually run, but it
# has NOT been re-run end-to-end after packaging (a full build is ~15-25 min).
# Expect the *bitstream SHA to differ* unless you use the exact same Vivado build
# (2018.3, SW Build 2405991) and the same machine class: place-and-route is not
# bit-reproducible across versions. Resource/timing numbers should reproduce
# within a few percent.
#
#   .\build_pl.ps1
#   .\build_pl.ps1 -Vivado 'D:\Vivado\Vivado\2018.3\bin\vivado.bat' -Work D:\pl_build_try
param(
    [string]$Vivado = 'D:\Vivado\Vivado\2018.3\bin\vivado.bat',
    [string]$Work = 'D:\pl_build_try',
    [switch]$SkipBitstreamCheck
)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$src  = Join-Path (Split-Path -Parent $here) 'src'
if (-not (Test-Path $Vivado)) { throw "Vivado not found: $Vivado" }

New-Item -ItemType Directory -Force -Path $Work, (Join-Path $Work 'logs'), (Join-Path $Work 'report') | Out-Null
$log = Join-Path $Work 'logs'

function RunVivado($tcl, $logName, $expect) {
    $t = Join-Path $src ('bd\' + $tcl)
    if (-not (Test-Path $t)) { throw "missing Tcl: $t" }
    Write-Host "`n[vivado] $tcl" -ForegroundColor Cyan
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & $Vivado -mode batch -source $t -log (Join-Path $log $logName) -journal (Join-Path $log ($logName -replace '\.log$', '.jou'))
    $rc = $LASTEXITCODE
    $sw.Stop()
    if ($rc -ne 0) { throw "$tcl failed rc=$rc (see $log\$logName)" }
    $txt = Get-Content (Join-Path $log $logName) -Raw
    if ($expect -and $txt -notmatch [regex]::Escape($expect)) {
        throw "$tcl finished but '$expect' not found in the log"
    }
    Write-Host ("[ok] {0} in {1:N1} s" -f $tcl, $sw.Elapsed.TotalSeconds) -ForegroundColor Green
}

RunVivado 'create_audio_pitch_dma.tcl' 'create.log' 'AUDIO_PITCH_DMA_VALIDATED'
RunVivado 'synth_2018_3.tcl'           'synth.log'  'AUDIO_PITCH_DMA_SYNTHESIZED_2018_3'
RunVivado 'impl_2018_3.tcl'            'impl.log'   'AUDIO_PITCH_DMA_BITSTREAM_BUILT_2018_3'
RunVivado 'export_hdf.tcl'             'export.log' 'HDF_EXPORTED'

# locate the products (the Tcl writes into <Work>\generated\...)
$bin = Get-ChildItem $Work -Recurse -Filter zynq_wrapper.bin -ErrorAction SilentlyContinue |
       Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $bin) { throw "zynq_wrapper.bin not found under $Work" }
Write-Host "`n[bin] $($bin.FullName)  $($bin.Length) B"

$swap = Join-Path $Work 'audio_pitch_dma_2018_swap.bin'
python (Join-Path $src 'make_swap.py') $bin.FullName $swap
if ($LASTEXITCODE -ne 0) { throw 'make_swap.py failed' }

Write-Host "`n[hashes] rebuild vs shipped" -ForegroundColor Cyan
$shipped = Join-Path (Split-Path -Parent $here) 'build\SHA256SUMS.txt'
foreach ($f in Get-ChildItem $Work -Recurse -Include zynq_wrapper.bit, zynq_wrapper.bin,
                                           audio_pitch_dma_2018_swap.bin, *.hdf) {
    $h = (Get-FileHash $f.FullName -Algorithm SHA256).Hash.ToLower()
    $known = if (Test-Path $shipped) {
        (Select-String -Path $shipped -Pattern ([regex]::Escape($f.Name)) |
         Select-Object -First 1).Line
    } else { $null }
    Write-Host ("{0,-34} {1}  {2}" -f $f.Name, $h.Substring(0,16), $(if ($known) { '(in SHA256SUMS)' } else { '' }))
}

if (-not $SkipBitstreamCheck) {
    Write-Host "`nCompare the numbers above with fpga/build/SHA256SUMS.txt."
    Write-Host "A different bitstream SHA is EXPECTED unless Vivado build + machine match."
}
Write-Host "`n[done] products under $Work" -ForegroundColor Green
