import numpy as np
D=r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime"
c=np.fromfile(D+r"\dmp_cn.bin",dtype="<f4")
r=np.fromfile(D+r"\ref_cn.bin",dtype="<f4")
print("cn first 20:")
print("C:",np.round(c[:20],5))
print("R:",np.round(r[:20],5))
print("cn samples 100-115:")
print("C:",np.round(c[100:115],5))
print("R:",np.round(r[100:115],5))
# base
cb=np.fromfile(D+r"\dmp_base.bin",dtype="<f4").reshape(13,384)
rb=np.fromfile(D+r"\ref_base.bin",dtype="<f4").reshape(13,384)
print("base frame 6 channel 0-10:")
print("C:",np.round(cb[6,:10],4))
print("R:",np.round(rb[6,:10],4))
