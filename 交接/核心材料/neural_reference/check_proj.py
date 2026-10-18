import numpy as np, struct
from pathlib import Path
t = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test")
c_e = np.fromfile(t/"dbg_e_dcc.bin", dtype=np.float32).reshape(13,512)
c_mem = np.fromfile(t/"dbg_mem.bin", dtype=np.float32).reshape(13,512)[:, :256]
p_e = np.fromfile(t/"pt_e_dcc.bin", dtype=np.float32).reshape(13,512)
p_mem = np.fromfile(t/"pt_mem.bin", dtype=np.float32).reshape(13,256)

mb = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\llvc_deploy_model.bin")
raw = open(mb,"rb").read()
float_off = struct.unpack("<I", raw[32:36])[0]
fa_off = np.frombuffer(raw[44:44+128*4], dtype=np.uint32)
def getw(idx, shape):
    off = fa_off[idx]; n = int(np.prod(shape))
    return np.frombuffer(raw, dtype=np.float32, count=n, offset=float_off+off).reshape(shape)
we = getw(105, (256,2)); be = getw(106, (256,))

def proj(e, w, b):
    out = np.zeros((13,256), dtype=np.float32)
    for tt in range(13):
        for c in range(256):
            v = w[c,0]*e[tt,2*c]+w[c,1]*e[tt,2*c+1]+b[c]
            out[tt,c] = v if v>0 else 0
    return out

man_ce = proj(c_e, we, be)
man_pe = proj(p_e, we, be)
print("manual(C.e) vs C mem maxdiff:", np.abs(man_ce-c_mem).max())
print("manual(P.e) vs P mem maxdiff:", np.abs(man_pe-p_mem).max())
