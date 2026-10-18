import numpy as np
t = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test"
c = np.fromfile(t+r"\dbg_encstate.bin", dtype=np.float32).reshape(510,512)
p = np.fromfile(t+r"\p22_encstate.bin", dtype=np.float32).reshape(510,512)
d = np.abs(c-p)
# per-frame max
fmax = d.max(axis=1)
bad = np.argwhere(fmax>0.001)
print("frames with >0.001 drift:", len(bad))
for fr in bad[:30]:
    fr=fr[0]
    ch=int(np.argmax(d[fr]))
    print("frame",fr,"maxdiff",round(float(fmax[fr]),4),"ch",ch,
          "ref",round(float(p[fr,ch]),4),"C",round(float(c[fr,ch]),4))
