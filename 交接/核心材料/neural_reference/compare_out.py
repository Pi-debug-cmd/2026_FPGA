import numpy as np
t = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test"
c = np.fromfile(t+r"\cout.bin", dtype=np.float32)
r = np.fromfile(t+r"\ref_quant_stream.bin", dtype=np.float32)
n = min(len(c), len(r))
e = c[:n]-r[:n]
print("C output vs quantized streaming ref:")
print("  maxdiff", float(np.abs(e).max()))
print("  overall SNR %.2f dB" % (10*np.log10(np.mean(r[:n]**2)/np.mean(e**2))))
# per-block SNR for the first 40 blocks (each 208 samples)
for b in range(40):
    s = b*208; seg = slice(s, s+208)
    rr = r[seg]; ee = c[seg]-rr
    if np.mean(rr**2) < 1e-10:
        snr = 999
    else:
        snr = 10*np.log10(np.mean(rr**2)/np.mean(ee**2))
    if b < 30 or snr < 40:
        print("  block %d maxdiff %.4f SNR %.1f" % (b, np.abs(ee).max(), snr))
