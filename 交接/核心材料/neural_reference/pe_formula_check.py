import numpy as np, math
c = 256
def c_pe(t):
    row = np.zeros(256, dtype=np.float32)
    for i in range(0,256,2):
        arg = t*math.exp(math.log(10000)*(-i)/256)
        row[i] = math.sin(arg); row[i+1] = math.cos(arg)
    return row
def sb_pe(t):
    pe = np.zeros(256, dtype=np.float32)
    denom = np.exp(np.arange(0,256,2)*(-math.log(10000)/256))
    pe[0::2] = np.sin(t*denom); pe[1::2] = np.cos(t*denom)
    return pe
for t in [0,1,13,14,25]:
    print("t",t,"maxdiff", np.abs(c_pe(t)-sb_pe(t)).max())
