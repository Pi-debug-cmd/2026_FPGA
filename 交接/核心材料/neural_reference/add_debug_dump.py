import io
p = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\llvc_runtime.c"
s = io.open(p, "r", encoding="utf-8", newline="").read()

# add a dump helper right before the process block function
helper_anchor = "// ---------- per-block (240 in = front32 + shifted208) ----------\n"
dump_helper = (
"// ---------- debug dump (first block only) ----------\n"
"static int dbg_blk = 0;\n"
"static void dbg_dump(const char *name, const float *x, size_t n) {\n"
"    if (dbg_blk != 0) return;\n"
"    char path[256];\n"
"    snprintf(path, sizeof(path),\n"
"      \"D:\\\\Tools_FPGA\\\\workspace\\\\voice_conversion_zynq7020\\\\deploy_runtime\\\\test\\\\dbg_%s.bin\", name);\n"
"    FILE *f = fopen(path, \"wb\");\n"
"    if (f) { fwrite(x, sizeof(float), n, f); fclose(f); }\n"
"}\n"
"// ---------- per-block (240 in = front32 + shifted208) ----------\n"
)
assert s.count(helper_anchor) == 1
s = s.replace(helper_anchor, dump_helper)

# at start of process block, increment dbg_blk
start_anchor = "void llvc_process_block(llvc_t *m, const float *block240, float *out208) {\n"
start_new = start_anchor + "    dbg_blk++;\n"
assert s.count(start_anchor) == 1
s = s.replace(start_anchor, start_new)

# dump cn after the final add (240)
anchor_cn = "    for (unsigned i = 0; i < 240; ++i) cn[i] = block240[i] + cn[i];\n"
assert s.count(anchor_cn) == 1
s = s.replace(anchor_cn, anchor_cn + "    dbg_dump(\"cn\", cn, 240);\n")

# dump e after in_conv (13*512)
anchor_e = "    // DCC encoder (8 blocks)\n"
assert s.count(anchor_e) == 1
s = s.replace(anchor_e, "    dbg_dump(\"e_inconv\", m->e, 13*512);\n" + anchor_e)

# dump l after label integration
anchor_l = "    // proj e2d_e / e2d_l"
assert s.count(anchor_l) == 1
s = s.replace(anchor_l, "    dbg_dump(\"l\", m->l, 13*512);\n" + anchor_l)

# dump mem/tgt after proj+relu (13*512 each, first 256 live)
anchor_dec = "    // decoder: prepend contexts -> 26 frames"
assert s.count(anchor_dec) == 1
s = s.replace(anchor_dec, "    dbg_dump(\"mem\", m->mem, 13*512);\n    dbg_dump(\"tgt\", m->tgt, 13*512);\n" + anchor_dec)

# dump outin before out_conv (17*512)
anchor_outconv = "    // out_conv: 17 frames -> 208 samples + tanh"
assert s.count(anchor_outconv) == 1
s = s.replace(anchor_outconv, "    dbg_dump(\"outin\", m->outin, 17*512);\n" + anchor_outconv)

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("debug dump instrumentation added")
