import numpy as np
t=r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test"
d=np.fromfile(t+r"\dbg_dcc3_densein.bin",dtype=np.float32).reshape(13,512)
cq=np.fromfile(t+r"\enc3_qin.bin",dtype=np.uint8).reshape(13,512)

# C's exact printed scale
sx_c = 0.03733256
# replicate C roundf (half away from zero)
def c_round(x):
    return np.sign(x)*np.floor(np.abs(x)+0.5)

q = c_round(d/sx_c)
q = np.clip(q,-128,127).astype(np.int8).view(np.uint8)
print("using C sx, half-away: n_diff", int(np.sum(q!=cq)), "of", q.size)

# also check with numpy's rint (half to even)
q2 = np.rint(d/sx_c)
q2 = np.clip(q2,-128,127).astype(np.int8).view(np.uint8)
print("using C sx, half-even: n_diff", int(np.sum(q2!=cq)), "of", q2.size)

# where do they differ
diff = np.argwhere(q!=cq)
print("first diffs (frame,ch): dump_val, requant, c_actual")
for fr,ch in diff[:10]:
    print(fr,ch, round(float(d[fr,ch]),5), int(q[fr,ch]), int(cq[fr,ch]))
