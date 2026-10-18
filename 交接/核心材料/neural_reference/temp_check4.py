import numpy as np
t=r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test"
bef=np.fromfile(t+r"\enc3_before.bin",dtype=np.float32)
din=np.fromfile(t+r"\dbg_dcc3_densein.bin",dtype=np.float32)
raw=np.fromfile(t+r"\enc3_rawin.bin",dtype=np.float32)
n=min(len(bef),len(din),len(raw))
print("before vs dcc3_densein maxdiff", float(np.abs(bef[:n]-din[:n]).max()))
print("before vs rawin(after) maxdiff", float(np.abs(bef[:n]-raw[:n]).max()))
