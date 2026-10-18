import numpy as np
D=r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime"
c=np.fromfile(D+r"\dmp_cn.bin",dtype="<f4")
r=np.fromfile(D+r"\ref_cn.bin",dtype="<f4")
# print every 8th sample
idx=np.arange(0,240,8)
print("idx   C_cn      R_cn")
for i in idx:
    print("%3d %8.5f %8.5f"%(i,c[i],r[i]))
# also the input block
one=np.fromfile(D+r"\test\one_loud_in.bin",dtype="<f4")
block=np.concatenate([np.zeros(32),one[16:224]])
print("block every 16:")
for i in np.arange(0,240,16):
    print("%3d %7.4f"%(i,block[i]))
