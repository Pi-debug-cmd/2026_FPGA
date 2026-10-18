import numpy as np
D=r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime"
c=np.fromfile(D+r"\out_pc_red.bin",dtype="<f4")
seg=c[2080:2720]
nfft=4096
sp=np.abs(np.fft.rfft(seg*np.hanning(len(seg)),nfft))
freqs=np.fft.rfftfreq(nfft,1/16000)
# all peaks above a threshold
import librosa
peaks=librosa.util.peak_pick(sp,pre_max=3,post_max=3,pre_avg=3,post_avg=3,delta=0.0005,wait=5)
for p in peaks:
    print("%.1f Hz  amp %.5f"%(freqs[p],sp[p]))
