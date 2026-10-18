import numpy as np
t = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test"
def db(n): return np.fromfile(t+"\\"+n, dtype=np.float32)
def cmp(a,b,name):
    e=a-b
    s=10*np.log10(np.mean(a**2)/np.mean(e**2)) if np.mean(a**2)>1e-12 else 999
    print("%s: SNR %.1f dB maxdiff %.4f RMS %.4f vs %.4f" % (name, s, np.abs(e).max(), np.sqrt(np.mean(a**2)), np.sqrt(np.mean(b**2))))
cmp(db("q22_outconv_in.bin"), db("dbg_outin.bin"), "outconv input")
cmp(db("q22_outconv_out.bin"), db("dbg_cn.bin") if False else None, "x") if False else None
# C output block22: extract from cout.bin
cout = db("cout.bin")[22*208:23*208]
cmp(db("q22_outconv_out.bin"), cout, "outconv output")
