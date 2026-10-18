import io
p = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\llvc_runtime.c"
s = io.open(p, "r", encoding="utf-8", newline="").read()

# Dump self-attn output (m->decout) right after self attention call
anchor1 = "              m->decout, m->q, m->kv, m->vv, m->attn);\n"
assert s.count(anchor1) == 1
s = s.replace(anchor1, anchor1 + "    dbg_dump(\"dec_self\", m->decout, 13*256);\n")

# Dump after self residual+norm (m->q)
anchor2 = "    layernorm(m->q, fa(m,FA_TF_BASE+6), fa(m,FA_TF_BASE+7), 13, 256);\n"
assert s.count(anchor2) == 1
s = s.replace(anchor2, anchor2 + "    dbg_dump(\"q_norm\", m->q, 13*256);\n")

# Dump cross-attn output (m->decout)
anchor3 = "              m->decout, m->q, m->kv, m->vv, m->attn);\n"
assert s.count(anchor3) == 1
s = s.replace(anchor3, anchor3 + "    dbg_dump(\"dec_cross\", m->decout, 13*256);\n")

# Dump after cross residual+norm (m->kv)
anchor4 = "    layernorm(m->kv, fa(m,FA_TF_BASE+8), fa(m,FA_TF_BASE+9), 13, 256);\n"
assert s.count(anchor4) == 1
s = s.replace(anchor4, anchor4 + "    dbg_dump(\"kv_norm\", m->kv, 13*256);\n")

# Dump FFN final (m->attn)
anchor5 = "    layernorm(m->attn, fa(m,FA_TF_BASE+10), fa(m,FA_TF_BASE+11), 13, 256);\n"
assert s.count(anchor5) == 1
s = s.replace(anchor5, anchor5 + "    dbg_dump(\"ffn_norm\", m->attn, 13*256);\n")

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("added decoder dumps")
