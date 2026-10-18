import numpy as np, librosa
D=r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime"
c=np.fromfile(D+r"\out_pc_red.bin",dtype="<f4")
# silence gap 1.3-1.7s
for nm,(a,b) in [("silence",(2080,2720)),("speech1",(800,1600)),("speech2",(4000,4800))]:
    seg=c[a:b]
    print(nm,"rms %.5f max %.5f"%(np.sqrt((seg**2).mean()),np.abs(seg).max()))
# spectrum of silence gap
seg=c[2080:2720]
nfft=2048
sp=np.abs(np.fft.rfft(seg*np.hanning(len(seg)),nfft))
freqs=np.fft.rfftfreq(nfft,1/16000)
idx=np.where((freqs>500)&(sp>sp.max()*0.2))[0]
print("silence-gap peaks >500Hz:"," ".join("%.0f"%freqs[i] for i in idx))
