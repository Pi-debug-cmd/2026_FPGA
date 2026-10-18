$src = 'D:\g_build\proj\zynq_gemm_irq.bin'
$dst = 'D:\g_build\proj\zynq_gemm_irq_swap.bin'
$b = [IO.File]::ReadAllBytes($src)
$rev = New-Object byte[] 256
for ($v = 0; $v -lt 256; $v++) {
    $r = 0
    for ($bit = 0; $bit -lt 8; $bit++) {
        if ($v -band (1 -shl $bit)) { $r = $r -bor (1 -shl (7 - $bit)) }
    }
    $rev[$v] = [byte]$r
}
for ($i = 0; $i -lt $b.Length; $i++) { $b[$i] = $rev[$b[$i]] }
[IO.File]::WriteAllBytes($dst, $b)
# verify sync at dword-aligned offsets
$found = -1
for ($i = 0; $i -le $b.Length - 4; $i += 4) {
    if ($b[$i] -eq 0x66 -and $b[$i + 1] -eq 0x55 -and $b[$i + 2] -eq 0x99 -and $b[$i + 3] -eq 0xAA) { $found = $i; break }
}
"sync_at_dword=$found"
"sha=" + (Get-FileHash $dst -Algorithm SHA256).Hash
"size=" + (Get-Item $dst).Length
