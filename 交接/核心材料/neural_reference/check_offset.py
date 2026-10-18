import numpy as np
t = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test"
c = np.fromfile(t+r"\cout.bin", dtype=np.float32)
r = np.fromfile(t+r"\ref_quant_stream.bin", dtype=np.float32)
n = min(len(c), len(r)); c=c[:n]; r=r[:n]
# speech region: blocks 22-60
s = 22*208; e = 60*208
cs = c[s:e]; rs = r[s:e]
print("speech-region direct corr", float(np.mean(cs*rs)/np.sqrt(np.mean(cs**2)*np.mean(rs**2))))
# cross-correlation for offsets -20..20
best=None
for off in range(-20,21):
    if off<0:
        a=cs[-off:]; b=rs[:off] if off<0 else rs
    if off>=0:
        a=cs[:len(cs)-off]; b=rs[off:off+len(a)]
    m=min(len(a),len(b)); a=a[:m]; b=b[:m]
    corr=np.mean(a*b)/np.sqrt(np.mean(a**2)*np.mean(b**2))
    if best is None or corr>best[1]: best=(off,corr)
print("best offset", best)
# overall RMS
print("C RMS", float(np.sqrt(np.mean(cs**2))), "ref RMS", float(np.sqrt(np.mean(rs**2))))
