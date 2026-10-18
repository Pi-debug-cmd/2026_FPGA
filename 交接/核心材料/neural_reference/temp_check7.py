import numpy as np
t=r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test"
c=np.fromfile(t+r"\dbg_dcc3_pwout.bin",dtype=np.float32)
r=np.fromfile(t+r"\ref_dcc3_pwout.bin",dtype=np.float32)
n=min(len(c),len(r))
print("C vs ref maxdiff", float(np.abs(c[:n]-r[:n]).max()))
