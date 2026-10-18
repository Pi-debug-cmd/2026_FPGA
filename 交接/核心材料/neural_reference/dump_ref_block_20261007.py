"""Reproduce block 22 in pure float using the model's actual weights, dump intermediates
matching the C names, then compare."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch
BASE=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR=BASE/"neural_reference"; BUD=BASE/"board_budget_20261005"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
from train_reduced_20261007 import build_net
from llvc_online_stream import LLVCAudioStream
net=build_net(NR/'LLVC/experiments/llvc/config_reduced.json')
ck=torch.load(BUD/'reduced_student_v2/final.pt',map_location='cpu',weights_only=True)
net.load_state_dict(ck['model'],strict=True); net.eval()
x=np.fromfile(BASE/"deploy_runtime/test/input.bin",dtype="<f4")
st=LLVCAudioStream(net)
# run blocks 0..21, then capture block 22 by manually running model forward with hooks
parts=st.feed(x[:22*208])  # feed first 22 chunks worth
# state after 22 blocks? feed processes pending. Let's just run full and hook block 22.
st2=LLVCAudioStream(net)
capt={}
def hook(name):
    def h(mod,inp,out):
        capt[name]=(inp,out)
    return h
hs=[]
hs.append(net.convnet_pre.register_forward_hook(hook("cn")))
hs.append(net.in_conv.register_forward_hook(hook("base")))
hs.append(net.mask_gen.encoder.register_forward_hook(hook("enc")))
hs.append(net.mask_gen.proj_e2d_e.register_forward_hook(hook("e2d_e")))
hs.append(net.mask_gen.proj_e2d_l.register_forward_hook(hook("e2d_l")))
hs.append(net.mask_gen.decoder.register_forward_hook(hook("dec")))
hs.append(net.mask_gen.proj_d2e.register_forward_hook(hook("d2e")))
hs.append(net.out_conv.register_forward_hook(hook("out")))
# monkeypatch model forward to count blocks and dump at 22
import types
orig_fwd=net.forward
count={"n":0}
def patched(*a,**k):
    res=orig_fwd(*a,**k)
    bn=count["n"]; count["n"]+=1
    if bn==22:
        outdir=BASE/"deploy_runtime"
        for nm in ["cn","base","enc","e2d_e","e2d_l","dec","d2e","out"]:
            o=capt[nm][1]
            o=o[0] if isinstance(o,tuple) else o
            print(nm, tuple(o.shape))
            o.detach().cpu().numpy().reshape(-1).tofile(outdir/("ref_%s_raw.bin"%nm))
        blk=a[0].reshape(-1).detach().numpy(); blk.tofile(outdir/"ref_block_input.bin")
    return res
net.forward=patched
st3=LLVCAudioStream(net)
p=st3.feed(x); p+=st3.finish()
print("blocks processed:",count["n"])
for h in hs: h.remove()
