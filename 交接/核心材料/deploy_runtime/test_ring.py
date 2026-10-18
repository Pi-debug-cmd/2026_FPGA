import numpy as np
# replicate ring vs linear depthwise for one block, 1 channel, many chunks
for (d,bl) in [(1,2),(2,4),(4,8),(8,16),(16,32),(32,64),(64,128),(128,256)]:
    R=bl+13
    nchunks=60
    # generate input frames (1 channel)
    frames=np.arange(nchunks*13,dtype=np.float32)
    # weights w[0],w[1],w[2]
    w=np.array([0.3,0.5,0.7])
    # LINEAR
    cbuf=np.zeros(bl,dtype=np.float32)
    lin_out=[]
    for c in range(nchunks):
        cur=frames[c*13:c*13+13]
        din=np.concatenate([cbuf,cur])
        for t in range(13):
            r0=din[t]; r1=din[t+d]; r2=din[t+2*d]
            lin_out.append(w[0]*r0+w[1]*r1+w[2]*r2)
        cbuf=din[13:13+bl]
    # RING
    ring=np.zeros(R,dtype=np.float32)
    head=0
    ring_out=[]
    for c in range(nchunks):
        cur=frames[c*13:c*13+13]
        for t in range(13):
            ring[(head+t)%R]=cur[t]
        for t in range(13):
            ic=(head+t)%R
            i1=(head+t-d)%R
            i2=(head+t-2*d)%R
            rc=ring[ic]; r1=ring[i1]; r2=ring[i2]
            ring_out.append(w[2]*rc+w[1]*r1+w[0]*r2)
        head=(head+13)%R
    lin_out=np.array(lin_out); ring_out=np.array(ring_out)
    diff=np.abs(lin_out-ring_out)
    print('d=%3d R=%3d maxdiff=%.4f  %s'%(d,R,diff.max(),'OK' if diff.max()<1e-3 else 'MISMATCH'))
    if diff.max()>=1e-3:
        idx=np.argmax(diff)
        print('   first mismatch at output idx',idx,'(chunk',idx//13,'t',idx%13,')')
        print('   lin',lin_out[idx],'ring',ring_out[idx])
