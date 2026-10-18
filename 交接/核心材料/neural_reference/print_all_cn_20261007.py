import numpy as np
D=r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime"
c=np.fromfile(D+r"\dmp_cn.bin",dtype="<f4")
r=np.fromfile(D+r"\ref_cn.bin",dtype="<f4")
print("all 240 C cn:")
for i in range(0,240,24):
    print("%3d:"%i," ".join("%7.4f"%x for x in c[i:i+24]))
print("all 240 R cn:")
for i in range(0,240,24):
    print("%3d:"%i," ".join("%7.4f"%x for x in r[i:i+24]))
