"""Full Python int8 streaming simulation (all blocks), matching the C normal path, to
verify the C final output and locate the discrepancy."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch
BASE=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR=BASE/"neural_reference"; BUD=BASE/"board_budget_20261005"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
from train_reduced_20261007 import build_net
net=build_net(NR/'LLVC/experiments/llvc/config_reduced.json')
ck=torch.load(BUD/'reduced_student_v2/final.pt',map_location='cpu',weights_only=True)
net.load_state_dict(ck['model'],strict=True); net.eval()
raw=open(BUD/"llvc_deploy_model_reduced.bin","rb").read()
hdr=np.frombuffer(raw[:4096],dtype="<u4")
mpo_off=11+128
mpo=np.frombuffer(raw,dtype="<u4",count=16,offset=4*mpo_off)
mso=np.frombuffer(raw,dtype="<u4",count=16,offset=4*(mpo_off+16))
packed_off=hdr[10]; scale_off=hdr[9]
def deq(mi,oc,ic):
    p=mpo[mi]; s=mso[mi]
    packed=np.frombuffer(raw,dtype=np.uint8,count=ic*512,offset=packed_off+p).reshape(ic,512)
    sw=np.frombuffer(raw,dtype="<f4",count=oc,offset=scale_off+s)
    return packed[:,:oc].astype(np.int8).T*sw[:,None]
def qd(x, W):
    # x [T,ic], W [oc,ic]
    amax=np.abs(x).max(); sx=amax/127
    qx=np.clip(np.round(x/sx),-128,127).astype(np.int8)
    return (qx@W.T)*sx
# Manual full streaming in float BUT with int8 pointwise (and later attention dense)
x=np.fromfile(BASE/"deploy_runtime/test/input.bin",dtype="<f4")
enc,dec,outb=net.init_buffers(1,'cpu'); pre=net.convnet_pre.init_ctx_buf(1,'cpu'); fr=torch.zeros(1,1,32)
L=16; cs=208; pending=x.copy(); outs=[]
with torch.inference_mode():
    while len(pending)>=cs+L:
        sh=torch.from_numpy(pending[L:L+cs]).reshape(1,1,-1)
        block=torch.cat((fr,sh),-1)
        # convnet
        cn=block.clone()
        for i in range(12):
            cin=torch.cat((pre[0:1,0:1,2*i:2*i+2],cn),-1)
            pre[0:1,0:1,2*i:2*i+2]=cin[...,-2:]
            cn=net.convnet_pre.down_convs[i](cin)
        xa=block+cn
        base=net.in_conv(xa)
        e=base.clone()
        for i in range(6):
            d=2**i; bl=2*d; start=2*(2**i-1)
            cin=torch.cat((enc[0:1,:,start:start+bl],e),-1)
            enc[0:1,:,start:start+bl]=cin[...,-bl:]
            dcc=net.mask_gen.encoder.dcc_layers[i]
            h2=dcc.layers[2](dcc.layers[1](dcc.layers[0](cin)))
            Wq=deq(i,384,384)
            hx=qd(h2[0].permute(1,0).numpy(),Wq)
            hx=torch.from_numpy(hx).permute(1,0)[None]
            e=e+dcc.layers[5](dcc.layers[4](hx))
        # label
        lconst=torch.from_numpy(np.fromfile(BASE/"deploy_runtime/dmp_l.bin",dtype="<f4")*0) # placeholder
        # use the model's label embedding constant
        le=net.label_embedding(torch.zeros(1,1))[0]
        l=le[None,:,None]*e
        # projections
        mr=net.mask_gen.proj_e2d_e(e); tr=net.mask_gen.proj_e2d_l(l)
        # decoder (use model's decoder with carried dec)
        mout,dec=net.mask_gen.decoder(tr,mr,dec)
        mout=net.mask_gen.proj_d2e(mout)
        mout=mout+l
        oi=torch.cat((outb, base*mout),-1)
        outb=oi[...,-4:]
        y=net.out_conv(oi)
        outs.append(y.reshape(-1).numpy())
        fr=sh[...,-32:].clone()
        pending=pending[cs:]
y=np.concatenate(outs)
np.fromfile(BASE/"deploy_runtime/out_pc_red.bin",dtype="<f4")
print("py int8-pointwise streaming len",len(y))
y.tofile(BASE/"deploy_runtime/out_py_int8enc.bin")
