"""Verify packed int8 weights match the model's float weights for each matrix."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys
BASE=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR=BASE/"neural_reference"; BUD=BASE/"board_budget_20261005"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
import torch, numpy as np
from train_reduced_20261007 import build_net
net=build_net(NR/'LLVC/experiments/llvc/config_reduced.json')
ck=torch.load(BUD/'reduced_student_v2/final.pt',map_location='cpu',weights_only=True)
net.load_state_dict(ck['model'],strict=True); net.eval()
sd=net.state_dict()
tl="mask_gen.decoder.tf_dec_layers.0"
# (name, float weight [oc,ic])
mats=[]
for i in range(6): mats.append(("enc%d"%i,sd[f"mask_gen.encoder.dcc_layers.dcc_{i}.layers.3.weight"][:,:,0]))
for att in ["self","multihead"]:
    ip=sd[f"{tl}.{att}_attn.in_proj_weight"]
    nm="self" if att=="self" else "cross"
    for q in ["q","k","v"]:
        mats.append((nm+"_"+q, ip[{"q":0,"k":1,"v":2}[q]*192:({"q":0,"k":1,"v":2}[q]+1)*192]))
    mats.append((nm+"_o",sd[f"{tl}.{att}_attn.out_proj.weight"]))
mats.append(("ffn1",sd[f"{tl}.linear1.weight"]))
mats.append(("ffn2",sd[f"{tl}.linear2.weight"]))
# read the packed binary
binpath=BUD/"llvc_deploy_model_reduced.bin"
raw=open(binpath,"rb").read()
hdr=np.frombuffer(raw[:4096],dtype="<u4")
# header layout: 8 I, then 3 I, then float_arr_off 128, mat_packed 16, mat_scale 16
mpo_off=11+128
mpo=np.frombuffer(raw,dtype="<u4",count=16,offset=4*mpo_off)
mso=np.frombuffer(raw,dtype="<u4",count=16,offset=4*(mpo_off+16))
packed_off=hdr[10]
scale_off=hdr[9]
for i,(name,W) in enumerate(mats):
    oc,ic=W.shape
    p=mpo[i]; s=mso[i]
    packed=np.frombuffer(raw,dtype=np.uint8,count=ic*512,offset=packed_off+p).reshape(ic,512)
    sw=np.frombuffer(raw,dtype="<f4",count=oc,offset=scale_off+s)
    Wq=packed[:, :oc].astype(np.int8).T   # [oc,ic]
    Wrec=Wq*sw[:,None]
    rel=np.abs(Wrec-W.numpy()).max()/np.abs(W.numpy()).max()
    print("%-8s oc%3d ic%3d max %.3f relerr %.5f"%(name,oc,ic,np.abs(W.numpy()).max(),rel))
