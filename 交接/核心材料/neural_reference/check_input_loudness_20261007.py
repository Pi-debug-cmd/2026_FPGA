"""Check input loudness in windows to understand the quiet start."""
import numpy as np
x=np.fromfile(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test\input.bin",dtype="<f4")
for i in range(0,12000,800):
    seg=x[i:i+800]
    print("samples %5d-%5d rms %.4f max %.3f"%(i,i+800,np.sqrt((seg**2).mean()),np.abs(seg).max()))
