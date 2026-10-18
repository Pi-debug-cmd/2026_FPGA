import io
p = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\llvc_runtime.c"
s = io.open(p, "r", encoding="utf-8", newline="").read()

# Add per-DCC-block dump after the residual add in the DCC loop.
# The residual add ends with:  m->e[...] += m->pwout[...];
# Find the closing of the residual add and insert a dump (first block only).
anchor = (
"        for (unsigned t = 0; t < 13; ++t)\n"
"            for (unsigned c = 0; c < 512; ++c)\n"
"                m->e[(size_t)t*512+c] += m->pwout[(size_t)t*512+c];\n"
"    }\n"
)
new = (
"        for (unsigned t = 0; t < 13; ++t)\n"
"            for (unsigned c = 0; c < 512; ++c)\n"
"                m->e[(size_t)t*512+c] += m->pwout[(size_t)t*512+c];\n"
"        if (dbg_blk == 1) {\n"
"            char nm[32]; snprintf(nm, sizeof(nm), \"e_dcc_%u\", i);\n"
"            dbg_dump(nm, m->e, 13*512);\n"
"        }\n"
"    }\n"
)
assert s.count(anchor) == 1
s = s.replace(anchor, new)
io.open(p, "w", encoding="utf-8", newline="").write(s)
print("added per-DCC-block dumps")
