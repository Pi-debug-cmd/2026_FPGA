import numpy as np
D=r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime"
b=np.fromfile(D+r"\dmp_block_input.bin",dtype="<f4")
# expected block: front 32 zeros + one_loud_in[16:224]
one=np.fromfile(D+r"\test\one_loud_in.bin",dtype="<f4")
exp=np.concatenate([np.zeros(32),one[16:224]])
print("block matches expected:",np.allclose(b,exp))
print("block[0:32] max:",np.abs(b[:32]).max())
print("block[32:240] max:",np.abs(b[32:]).max())
print("block every 16:")
for i in range(0,240,16): print("%3d %7.4f"%(i,b[i]))
