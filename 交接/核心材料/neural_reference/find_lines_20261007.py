"""Find the exact frequencies of the horizontal-line artifacts in the C output."""
import numpy as np, librosa
D=r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime"
c=np.fromfile(D+r"\out_pc_red.bin",dtype="<f4")
# use the silence gap 1.3-1.7s (samples 2080..2720)
seg=c[2080:2720]
# but the gap is quiet; artifacts show during speech. use a short speech region
seg=c[8000:12000]
win=np.hanning(4000)
sp=np.abs(np.fft.rfft(seg*win,8000))
freqs=np.fft.rfftfreq(8000,1/16000)
# find peaks
peaks=librosa.util.peak_pick(sp,pre_max=5,post_max=5,pre_avg=5,post_avg=5,
    delta=0.02,wait=10)
pk=sorted(peaks,key=lambda p:-sp[p])[:25]
print("artifact peak frequencies (Hz):")
print(" ".join("%.0f"%freqs[p] for p in sorted(pk)))
