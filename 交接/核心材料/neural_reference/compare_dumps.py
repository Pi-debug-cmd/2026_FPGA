import numpy as np
from pathlib import Path
t = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test")
pairs = [
    ("cn", 240),
    ("e_inconv", 13*512),
    ("l", 13*512),
    ("mem", 13*512),
    ("tgt", 13*512),
    ("outin", 17*512),
]
for name, n in pairs:
    c = np.fromfile(t/f"dbg_{name}.bin", dtype=np.float32)
    p = np.fromfile(t/f"pt_{name}.bin", dtype=np.float32)
    m = min(len(c), len(p), n)
    e = c[:m]-p[:m]
    if np.mean(p[:m]**2) > 1e-12:
        snr = 10*np.log10(np.mean(p[:m]**2)/np.mean(e**2))
    else:
        snr = float('inf')
    print(f"{name:10s} cmax={np.abs(c).max():.4f} pmax={np.abs(p).max():.4f} "
          f"maxdiff={np.abs(e).max():.5f} SNR={snr:.2f}dB")
