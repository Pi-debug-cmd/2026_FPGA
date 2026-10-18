import numpy as np
t = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test"
f = np.fromfile(t+r"\ref_float_stream.bin", dtype=np.float32)
q = np.fromfile(t+r"\ref_quant_stream.bin", dtype=np.float32)
c = np.fromfile(t+r"\cout.bin", dtype=np.float32)
n = min(len(f),len(q),len(c)); f=f[:n]; q=q[:n]; c=c[:n]
def snr(a,b,name):
    e=a-b
    print("%s: SNR %.2f dB maxdiff %.4f" % (name, 10*np.log10(np.mean(a**2)/np.mean(e**2)), np.abs(e).max()))
snr(f,q,"float vs quant")
snr(c,q,"C vs quant")
snr(c,f,"C vs float")
# speech region only (blocks 22-60)
s=22*208; e=60*208
def snr2(a,b,name):
    aa=a[s:e]; bb=b[s:e]; er=aa-bb
    print("%s (speech): SNR %.2f dB maxdiff %.4f RMSa %.4f RMSb %.4f" % (name, 10*np.log10(np.mean(aa**2)/np.mean(er**2)), np.abs(er).max(), np.sqrt(np.mean(aa**2)), np.sqrt(np.mean(bb**2))))
snr2(f,q,"float vs quant")
snr2(c,q,"C vs quant")
snr2(c,f,"C vs float")
