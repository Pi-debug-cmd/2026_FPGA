import io
p = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\llvc_runtime.c"
s = io.open(p, "r", encoding="utf-8", newline="").read()

# C: dump e right after DCC encoder loop, before label integration
anchor = "    // label integration: l = lconst * e\n"
assert s.count(anchor) == 1
s = s.replace(anchor, "    dbg_dump(\"e_dcc\", m->e, 13*512);\n" + anchor)

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("C: added e_dcc dump")
