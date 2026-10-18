import numpy as np, torch
t=r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test"
d=np.fromfile(t+r"\dbg_dcc3_densein.bin",dtype=np.float32)
cq=np.fromfile(t+r"\enc3_qin.bin",dtype=np.uint8)
dt=torch.from_numpy(d.reshape(13,512))
amax=dt.abs().amax(); sx=amax/127
dq=torch.round(dt/sx).clamp(-128,127).to(torch.int8)
dqb=dq.numpy().view(np.uint8).reshape(-1)
print("C dump requant vs C qin n_diff", int(np.sum(cq[:len(dqb)]!=dqb)), "of", len(dqb))
