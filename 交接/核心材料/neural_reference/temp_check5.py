import numpy as np
t=r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test"
bef=np.fromfile(t+r"\enc3_before.bin",dtype=np.float32)
din=np.fromfile(t+r"\dbg_dcc3_densein.bin",dtype=np.float32)
n=min(len(bef),len(din))
print("before vs dcc3_densein maxdiff", float(np.abs(bef[:n]-din[:n]).max()))
# now quantize the before dump and compare to C qin
cq=np.fromfile(t+r"\enc3_qin.bin",dtype=np.uint8).reshape(13,512)
ar=bef.reshape(13,512)
amax=np.abs(ar).max(); sx=amax/127
def cr(x): return np.sign(x)*np.floor(np.abs(x)+0.5)
q=np.clip(cr(ar/float(sx)),-128,127).astype(np.int8).view(np.uint8)
print("before requant vs C qin n_diff", int(np.sum(q!=cq)))
