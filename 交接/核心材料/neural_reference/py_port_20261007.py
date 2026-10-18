"""Pure-Python port of the C runtime (float), using the packed weights, to isolate
structure vs int8 quantization. Compares each stage to the R model at block 22."""
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
sd=net.state_dict()

# Manually reproduce block 22 using the model's float weights and carried state.
# First, run streaming to block 22 to obtain carried state.
x=np.fromfile(BASE/"deploy_runtime/test/input.bin",dtype="<f4")
enc,dec,outb=net.init_buffers(1,'cpu')
pre=net.convnet_pre.init_ctx_buf(1,'cpu')
front=torch.zeros(1,1,32)
L=16; cs=208
pending=np.empty(0)
def consume(pending, enc,dec,outb,pre,front, stop_at=None, dump=False):
    outs=[]; bn=0
    while len(pending)>=cs+L:
        shifted=torch.from_numpy(pending[L:L+cs]).reshape(1,1,-1)
        block=torch.cat((front,shifted),dim=-1)
        if dump and bn==stop_at:
            return pending,enc,dec,outb,pre,front,block,outs
        with torch.inference_mode():
            speech,enc,dec,outb,pre=net(block,enc,dec,outb,pre,pad=False)
        front=shifted[..., -2*L:].clone()
        pending=pending[cs:]
        outs.append(speech.reshape(-1).numpy()); bn+=1
    return pending,enc,dec,outb,pre,front,None,outs
pending=x[:23*208+16]
pending,enc,dec,outb,pre,front,block,_=consume(pending,enc,dec,outb,pre,front,stop_at=22,dump=True)
print("block rms %.4f matches ref: %s"%(np.sqrt((block.numpy()**2).mean()),
      np.allclose(block.numpy().reshape(-1),np.fromfile(BASE/"deploy_runtime/ref_block_input.bin",dtype="<f4"))))
# Now manually run convnet_pre with float weights and carried pre ctx.
def convnet_manual(x, pre):
    # x [1,1,T], pre [1,1,24]
    xn=x.clone()
    for i in range(12):
        ctx=pre[0:1,0:1,2*i:2*i+2]
        cin=torch.cat((ctx,xn),dim=-1)
        pre[0:1,0:1,2*i:2*i+2]=cin[..., -2:]
        rb=net.convnet_pre.down_convs[i]
        xn=rb(cin)
    return xn, pre
with torch.inference_mode():
    cn_man,pre=convnet_manual(block, pre)
    # skip add
    x_after=block+cn_man
    print("manual convnet (x_after) rms %.4f, C dmp_cn rms %.4f"%(
      np.sqrt((x_after.numpy()**2).mean()),
      np.sqrt((np.fromfile(BASE/"deploy_runtime/dmp_cn.bin",dtype="<f4")**2).mean())))
    print("matches C dmp_cn:",np.allclose(x_after.numpy().reshape(-1),
      np.fromfile(BASE/"deploy_runtime/dmp_cn.bin",dtype="<f4"),atol=1e-5))

# in_conv (manual, float): x_after [1,1,240] -> [1,384,13]
with torch.inference_mode():
    base=net.in_conv(x_after)
    print("base matches C:",np.allclose(base[0].permute(1,0).numpy().reshape(-1),
      np.fromfile(BASE/"deploy_runtime/dmp_base.bin",dtype="<f4"),atol=1e-6))
    # DCC encoder manual with carried enc state (enc [1,384,126])
    e=base.clone()
    r_enc=torch.from_numpy(np.fromfile(BASE/"deploy_runtime/ref_enc_raw.bin",dtype="<f4")).reshape(384,13)[None]
    for i in range(6):
        d=2**i; bl=2*d
        start=2*(2**i-1)
        ctx=enc[0:1,:, start:start+bl]
        din=torch.cat((ctx,e),dim=-1)
        enc[0:1,:,start:start+bl]=din[..., -bl:]
        dcc=net.mask_gen.encoder.dcc_layers[i]
        dccout=dcc(din)
        e=e+dccout
    print("py float e_after_enc vs R ref_enc: corr %.5f, allclose %s"%(
      np.corrcoef(e[0].permute(1,0).numpy().reshape(-1),r_enc[0].permute(1,0).numpy().reshape(-1))[0,1],
      np.allclose(e[0].permute(1,0).numpy().reshape(-1),r_enc[0].permute(1,0).numpy().reshape(-1),atol=1e-4)))
    print("py float e_after_enc vs C dmp: corr %.5f"%(
      np.corrcoef(e[0].permute(1,0).numpy().reshape(-1),
      np.fromfile(BASE/"deploy_runtime/dmp_e_after_enc.bin",dtype="<f4"))[0,1]))
