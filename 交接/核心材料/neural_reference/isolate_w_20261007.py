"""Run the float encoder port but with dequantized int8 pointwise weights to isolate
weight quantization vs activation quantization."""
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
# read packed weights/scales for enc0-5
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
    return packed[:,:oc].astype(np.int8).T*sw[:,None]  # [oc,ic]
# reconstruct carried state to block 22
x=np.fromfile(BASE/"deploy_runtime/test/input.bin",dtype="<f4")
enc,dec,outb=net.init_buffers(1,'cpu'); pre=net.convnet_pre.init_ctx_buf(1,'cpu')
front=torch.zeros(1,1,32); L=16; cs=208; pending=np.empty(0)
block=torch.from_numpy(np.fromfile(BASE/"deploy_runtime/ref_block_input.bin",dtype="<f4")).reshape(1,1,-1)
# We need carried enc/pre/front at block 22. Re-run streaming to 22.
enc2,dec2,out2=net.init_buffers(1,'cpu'); pre2=net.convnet_pre.init_ctx_buf(1,'cpu'); fr2=torch.zeros(1,1,32)
pend=x[:22*208]
with torch.inference_mode():
    b=0
    while len(pend)>=cs+L:
        sh=torch.from_numpy(pend[L:L+cs]).reshape(1,1,-1)
        bl=torch.cat((fr2,sh),-1)
        _,enc2,dec2,out2,pre2=net(bl,enc2,dec2,out2,pre2,pad=False)
        fr2=sh[...,-32:].clone(); pend=pend[cs:]; b+=1
print("replayed blocks:",b)
# manual convnet + in_conv to block 22
with torch.inference_mode():
    def convnet(x,pre):
        xn=x.clone()
        for i in range(12):
            cin=torch.cat((pre[0:1,0:1,2*i:2*i+2],xn),-1)
            pre[0:1,0:1,2*i:2*i+2]=cin[...,-2:]
            xn=net.convnet_pre.down_convs[i](cin)
        return xn
    cn=convnet(block,pre2); xa=block+cn
    base=net.in_conv(xa)
    e=base.clone()
    def q_dense(din, Wq, bias):
        # din [1,384,T], Wq [oc,ic], global activation scale
        x=din[0].permute(1,0).numpy()  # [T,ic]
        amax=np.abs(x).max(); sx=amax/127
        qx=np.clip(np.round(x/sx),-128,127).astype(np.int8)
        acc=qx@Wq.T
        y=acc*sx
        return torch.from_numpy(y).permute(1,0)[None]
    for i in range(6):
        d=2**i; bl=2*d; start=2*(2**i-1)
        ctx=enc2[0:1,:,start:start+bl]
        din=torch.cat((ctx,e),-1)
        enc2[0:1,:,start:start+bl]=din[...,-bl:]
        dcc=net.mask_gen.encoder.dcc_layers[i]
        Wq=deq(i,384,384)
        # depthwise+LN+ReLU via dcc.layers[0..2]
        h0=dcc.layers[0](din); h1=dcc.layers[1](h0); h2=dcc.layers[2](h1)
        # pointwise with int8 activation
        pw_raw=q_dense(h2, Wq, None)
        # LN+ReLU
        h3=dcc.layers[4](pw_raw); h4=dcc.layers[5](h3)
        e=e+h4
    r_enc=torch.from_numpy(np.fromfile(BASE/"deploy_runtime/ref_enc_raw.bin",dtype="<f4")).reshape(384,13)[None]
    print("int8-W int8-A encoder vs R: corr %.5f"%np.corrcoef(e[0].permute(1,0).reshape(-1).numpy(),
      r_enc[0].permute(1,0).reshape(-1).numpy())[0,1])
    print("int8-W int8-A encoder vs C dmp: corr %.5f"%np.corrcoef(e[0].permute(1,0).reshape(-1).numpy(),
      np.fromfile(BASE/"deploy_runtime/dmp_e_after_enc.bin",dtype="<f4"))[0,1])
