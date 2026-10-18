import numpy as np
t=r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test"
for cn,rn in [("din3","ref_din3"),("dcc3_dw","ref_dcc3_dw"),("dcc3_densein","ref_dcc3_densein"),("dcc3_pwout","ref_dcc3_pwout"),("dcc3_ln2","ref_dcc3_ln2")]:
    c=np.fromfile(t+r"\dbg_%s.bin"%cn,dtype=np.float32)
    q=np.fromfile(t+r"\%s.bin"%rn,dtype=np.float32)
    n=min(len(c),len(q)); e=c[:n]-q[:n]
    print("%-15s maxdiff %.6f SNR %.2f"%(cn,np.abs(e).max(),10*np.log10(np.mean(q[:n]**2)/np.mean(e**2))))
