# Prepare the fpga_manager image: 4-byte word swap + gzip, with hashes logged.
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$bin = Join-Path $root 'bitstream\stft_dma.bin'
if (-not (Test-Path $bin)) { throw "missing $bin" }
$out = Join-Path $root 'bitstream\stft_dma_swap.bin'
python (Join-Path $root 'tools\make_swap.py') $bin $out *> (Join-Path $root 'logs\make_swap.log')
if ($LASTEXITCODE -ne 0) { throw "make_swap failed" }
Get-Content (Join-Path $root 'logs\make_swap.log') | Write-Host
Get-ChildItem (Join-Path $root 'bitstream') | Where-Object { $_.Name -like 'stft_dma*' } |
    Select-Object Name, Length | Format-Table -AutoSize
