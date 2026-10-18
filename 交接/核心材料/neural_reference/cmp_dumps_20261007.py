import numpy as np
D=r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime"
def load(n): return np.fromfile(D+"\\"+n,dtype="<f4")
def cmp(name, c, r):
    n=min(len(c),len(r))
    c=c[:n]; r=r[:n]
    cr=np.corrcoef(c,r)[0,1] if c.std()>0 and r.std()>0 else 0
    rel=np.abs(c-r).max()/(np.abs(r).max()+1e-9)
    print("%-16s C rms %.4f R rms %.4f corr %.4f maxrelerr %.4f"%(
        name, np.sqrt((c**2).mean()), np.sqrt((r**2).mean()), cr, rel))
# cn (240, both linear)
cmp("cn",load("dmp_cn.bin"),load("ref_cn_raw.bin"))
# base: C frame-major [t*c], R channel-major [1,c,t]
rb=load("ref_base_raw.bin").reshape(384,13).T.reshape(-1)
cmp("base",load("dmp_base.bin"),rb)
# enc
re=load("ref_enc_raw.bin").reshape(384,13).T.reshape(-1)
cmp("e_after_enc",load("dmp_e_after_enc.bin"),re)
# decoder output = attn_after_ffn (C frame-major)
rd=load("ref_dec_raw.bin").reshape(192,13).T.reshape(-1)
cmp("attn_after_ffn",load("dmp_attn_after_ffn.bin"),rd)
# d2e: C mout is AFTER skip add of l; R d2e is before skip. Compare structure anyway.
r2=load("ref_d2e_raw.bin").reshape(384,13).T.reshape(-1)
cmp("mout(vs d2e)",load("dmp_mout.bin"),r2)
# final output
cmp("out208",load("dmp_block_input.bin")*0+np.nan, load("ref_out_raw.bin"))
