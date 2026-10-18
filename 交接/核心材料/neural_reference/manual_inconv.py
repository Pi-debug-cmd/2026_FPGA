import numpy as np
from pathlib import Path
t = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test")
cn = np.fromfile(t/"dbg_cn.bin", dtype=np.float32)
c = np.fromfile(t/"dbg_e_inconv.bin", dtype=np.float32).reshape(13,512)
p = np.fromfile(t/"pt_e_inconv.bin", dtype=np.float32).reshape(13,512)

# weight from binary
import struct
mb = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\llvc_deploy_model.bin")
raw = open(mb,"rb").read()
float_off = struct.unpack("<I", raw[32:36])[0]
fa_off = np.frombuffer(raw[44:44+128*4], dtype=np.uint32)
off = fa_off[48]
w = np.frombuffer(raw, dtype=np.float32, count=512*48,
                  offset=float_off+off).reshape(512,48)

# manual numpy conv: frame t, channel c = w[c] . cn[t*16:t*16+48]
manual = np.zeros((13,512), dtype=np.float32)
for tt in range(13):
    seg = cn[tt*16:tt*16+48]
    manual[tt] = w @ seg
manual = np.maximum(manual, 0)

print("manual vs C maxdiff:", np.abs(manual-c).max())
print("manual vs PT maxdiff:", np.abs(manual-p).max())
print("manual frame0 first 10:", manual[0,:10])
print("PT frame0 first 10:", p[0,:10])
