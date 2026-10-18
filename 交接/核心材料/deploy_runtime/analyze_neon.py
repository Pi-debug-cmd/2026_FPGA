import numpy as np, sys, wave
rt='D:/Tools_FPGA/workspace/voice_conversion_zynq7020/deploy_runtime/'
neon=np.fromfile(rt+'out_neon.bin',dtype=np.float32)
inp=np.fromfile(rt+'test/input.bin',dtype=np.float32)
print('neon',neon.shape,'min %.4f max %.4f rms %.4f'%(neon.min(),neon.max(),np.sqrt((neon**2).mean())))
print('input',inp.shape,'min %.4f max %.4f rms %.4f'%(inp.min(),inp.max(),np.sqrt((inp**2).mean())))
# save wav
def savew(x,name):
    y=np.clip(x,-1,1)
    pcm=(y*32767).astype(np.int16)
    w=wave.open(name,'wb');w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
    w.writeframes(pcm.tobytes());w.close()
savew(neon,rt+'out_neon.wav')
print('saved out_neon.wav')
# silence/noise check
n=len(neon)
seg=n//8
print('segment RMS:')
for i in range(8):
    s=neon[i*seg:(i+1)*seg]
    print('  seg%d rms %.4f'%(i,np.sqrt((s**2).mean())))
