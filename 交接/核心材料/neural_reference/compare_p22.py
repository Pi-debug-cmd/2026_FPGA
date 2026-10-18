import numpy as np
t = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test"
def db(n):
    return np.fromfile(t+"\\"+n, dtype=np.float32)
def snr(a,b):
    e=a-b
    if np.mean(a**2) < 1e-12: return 999, float(np.abs(e).max())
    return float(10*np.log10(np.mean(a**2)/np.mean(e**2))), float(np.abs(e).max())

# encoder state at block22
c_enc = db("dbg_encstate.bin")
p_enc = db("p22_encstate.bin")
print("encstate: SNR %.1f dB maxdiff %.2e" % snr(p_enc, c_enc))

# cn
c_cn = db("dbg_cn.bin")
p_cn = db("p22_cn.bin")
print("cn: SNR %.1f dB maxdiff %.2e" % snr(p_cn, c_cn))

# in_conv
c_inc = db("dbg_e_inconv.bin")
p_inc = db("p22_inconv.bin")
print("inconv: SNR %.1f dB maxdiff %.2e" % snr(p_inc, c_inc))

# per DCC
for i in range(8):
    c = db("dbg_e_dcc_%d.bin"%i)
    p = db("p22_dcc_%d.bin"%i)
    s, m = snr(p, c)
    print("DCC%d: SNR %.1f dB maxdiff %.4f" % (i, s, m))
