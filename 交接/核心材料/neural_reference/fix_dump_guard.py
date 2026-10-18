import io
p = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\llvc_runtime.c"
s = io.open(p, "r", encoding="utf-8", newline="").read()
old = "    if (dbg_blk != 0) return;\n"
new = "    if (dbg_blk != 1) return;\n"
assert s.count(old) == 1
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8", newline="").write(s)
print("guard fixed")
