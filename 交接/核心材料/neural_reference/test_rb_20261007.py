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
# block 22 input
blk=np.fromfile(BASE/"deploy_runtime/ref_block_input.bin",dtype="<f4")
x=torch.from_numpy(blk).reshape(1,1,-1)
pre=net.convnet_pre.init_ctx_buf(1,'cpu')
# need to run 22 blocks to set pre; instead just run this block with zero pre to inspect
co,pre2=net.convnet_pre(x, pre)
print("convnet_out rms %.5f, input rms %.5f"%(co.norm()/np.sqrt(co.numel()), x.norm()/np.sqrt(x.numel())))
print("convnet_out[0,0,:10]:",co[0,0,:10].tolist())
# ResidualBlock direct
rb=net.convnet_pre.down_convs[0]
conv_in=torch.cat((pre[0:1,0:1,0:2],x),dim=-1)
print("conv_in shape",conv_in.shape)
out=rb(conv_in)
print("rb output rms %.5f, [0,:10]:"%(out.norm()/np.sqrt(out.numel())),out[0,0,:10].tolist())
# manually: x[2:] + residual
res=torch.tanh(rb.filter(conv_in))*torch.sigmoid(rb.gate(conv_in))
manual=conv_in[...,2:]+res
print("manual matches rb:",torch.allclose(out,manual))
print("manual rms %.5f"%(manual.norm()/np.sqrt(manual.numel())))
