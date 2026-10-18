import numpy as np
from pathlib import Path
t = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test")
c = np.fromfile(t/"dbg_e_inconv.bin", dtype=np.float32).reshape(13,512)
p = np.fromfile(t/"pt_e_inconv.bin", dtype=np.float32).reshape(13,512)
# compare C frame t to PyTorch frame t and t-1/t+1
for fr in range(4):
    for shift in (-1,0,1):
        src = fr+shift
        if 0 <= src < 13:
            d = np.abs(c[fr]-p[src]).max()
            print(f"C frame {fr} vs PT frame {src}: maxdiff {d:.5f}")
    print()
# Check: is C just ReLU applied differently? fraction nonzero
print("C nonzero frac per frame 0:", (c[0]!=0).mean(), "PT:", (p[0]!=0).mean())
print("C frame0 first 10:", c[0,:10])
print("PT frame0 first 10:", p[0,:10])
