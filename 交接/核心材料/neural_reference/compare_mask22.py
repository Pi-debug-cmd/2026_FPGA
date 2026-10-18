import numpy as np
t = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test"
def db(n): return np.fromfile(t+"\\"+n, dtype=np.float32)
def cmp(a,b,name):
    e=a-b
    s=10*np.log10(np.mean(a**2)/np.mean(e**2)) if np.mean(a**2)>1e-12 else 999
    print("%s: SNR %.1f dB maxdiff %.4f RMS %.4f vs %.4f" % (name, s, np.abs(e).max(), np.sqrt(np.mean(a**2)), np.sqrt(np.mean(b**2))))
cmp(db("q22_mask.bin"), db("dbg_mout.bin"), "mask")
cmp(db("q22_e.bin"), db("dbg_e_dcc.bin"), "encoder e")
cmp(db("q22_l2.bin"), db("dbg_l.bin"), "l2")
