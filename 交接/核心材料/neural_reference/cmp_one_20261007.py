import numpy as np
c=np.fromfile(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\one_loud_c.bin",dtype="<f4")[:208]
r=np.fromfile(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test\one_loud_ref.bin",dtype="<f4")
print("c rms %.4f max %.4f  ref rms %.4f max %.4f"%(np.sqrt((c**2).mean()),np.abs(c).max(),
    np.sqrt((r**2).mean()),np.abs(r).max()))
print("corr %.4f"%np.corrcoef(c,r)[0,1])
print("c[:20]",np.round(c[:20],4))
print("r[:20]",np.round(r[:20],4))
