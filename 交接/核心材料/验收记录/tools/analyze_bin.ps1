$b = [IO.File]::ReadAllBytes('D:\g_build\proj\zynq_gemm_irq.bin')
$ca = 0; $c99 = 0; $c55 = 0; $c66 = 0
foreach ($x in $b) {
    if ($x -eq 0xAA) { $ca++ }
    elseif ($x -eq 0x99) { $c99++ }
    elseif ($x -eq 0x55) { $c55++ }
    elseif ($x -eq 0x66) { $c66++ }
}
"AA=$ca 99=$c99 55=$c55 66=$c66"
for ($i = 0; $i -lt $b.Length; $i++) {
    if ($b[$i] -eq 0xAA) {
        $end = $i + 15
        if ($end -ge $b.Length) { $end = $b.Length - 1 }
        $seg = @()
        for ($k = $i; $k -le $end; $k++) { $seg += $b[$k].ToString('X2') }
        "firstAA=$i seg: $($seg -join ' ')"
        break
    }
}
