import numpy as np
rt='D:/Tools_FPGA/workspace/voice_conversion_zynq7020/deploy_runtime/'
ref=np.fromfile(rt+'out_pc_ref.bin',dtype=np.float32)
neon=np.fromfile(rt+'out_neon.bin',dtype=np.float32)
n=len(ref)
print('comparing first %d samples (%.2f s)'%(n,n/16000))
r=ref[:n]; a=neon[:n]
diff=np.abs(r-a)
print('max abs diff %.5f'%diff.max())
print('mean abs diff %.5f'%diff.mean())
print('ref rms %.4f  neon rms %.4f'%(np.sqrt((r**2).mean()),np.sqrt((a**2).mean())))
# correlation
cr=r-r.mean(); ca=a-a.mean()
corr=(cr*ca).sum()/np.sqrt((cr**2).sum()*(ca**2).sum())
print('waveform correlation %.5f'%corr)
# per-chunk (208) max diff to find localized errors
nc=n//208
worst=[]
for i in range(nc):
    d=np.abs(r[i*208:(i+1)*208]-a[i*208:(i+1)*208]).max()
    worst.append((d,i))
worst.sort(reverse=True)
print('worst chunks:',[(i,round(d,4)) for d,i in worst[:5]])
