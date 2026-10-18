import numpy as np
D=r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime"
c=np.fromfile(D+r"\dmp_block_input.bin",dtype="<f4")
r=np.fromfile(D+r"\ref_block_input.bin",dtype="<f4")
print("block input match:",np.allclose(c,r), "corr",np.corrcoef(c,r)[0,1])
print("C rms %.4f R rms %.4f"%(np.sqrt((c**2).mean()),np.sqrt((r**2).mean())))
# cn comparison detail
cc=np.fromfile(D+r"\dmp_cn.bin",dtype="<f4")
rr=np.fromfile(D+r"\ref_cn_raw.bin",dtype="<f4")
print("cn C[0:10]:",cc[:10])
print("cn R[0:10]:",rr[:10])
print("cn C[32:42]:",cc[32:42])
print("cn R[32:42]:",rr[32:42])
