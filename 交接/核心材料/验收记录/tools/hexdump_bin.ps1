$b = [IO.File]::ReadAllBytes('D:\g_build\proj\zynq_gemm_irq.bin')
for ($i = 0; $i -lt 96; $i += 16) {
    $seg = @()
    for ($k = $i; $k -lt ($i + 16); $k++) { $seg += $b[$k].ToString('X2') }
    $hex = $seg -join ' '
    $asc = -join ($b[$i..($i + 15)] | ForEach-Object { if ($_ -ge 32 -and $_ -le 126) { [char]$_ } else { '.' } })
    "{0:X4}: {1}  {2}" -f $i, $hex, $asc
}
