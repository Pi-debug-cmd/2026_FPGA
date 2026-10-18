import io
p = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\llvc_runtime.c"
s = io.open(p, "r", encoding="utf-8", newline="").read()

old1 = (
"        for (unsigned c = 0; c < 256; ++c) {\n"
"            mr[c] = pew[c*2]*er[c]+pew[c*2+1]*er[c+256];\n"
"            tr[c] = plw[c*2]*lr[c]+plw[c*2+1]*lr[c+256];\n"
"        }\n"
)
new1 = (
"        for (unsigned c = 0; c < 256; ++c) {\n"
"            mr[c] = pew[c*2]*er[2*c]+pew[c*2+1]*er[2*c+1];\n"
"            tr[c] = plw[c*2]*lr[2*c]+plw[c*2+1]*lr[2*c+1];\n"
"        }\n"
)
assert s.count(old1) == 1, s.count(old1)
s = s.replace(old1, new1)

old2 = (
"    for (unsigned t = 0; t < 13; ++t) {\n"
"        const float *ar = m->attn + (size_t)t*512;\n"
"        float *mr = m->mout + (size_t)t*512;\n"
"        for (unsigned c = 0; c < 512; ++c) mr[c] = pdw[c]*ar[c];\n"
"    }\n"
)
new2 = (
"    for (unsigned t = 0; t < 13; ++t) {\n"
"        const float *ar = m->attn + (size_t)t*512;\n"
"        float *mr = m->mout + (size_t)t*512;\n"
"        for (unsigned c = 0; c < 256; ++c) {\n"
"            mr[2*c]   = pdw[2*c]*ar[c];\n"
"            mr[2*c+1] = pdw[2*c+1]*ar[c];\n"
"        }\n"
"    }\n"
)
assert s.count(old2) == 1, s.count(old2)
s = s.replace(old2, new2)

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("patched projections OK")
