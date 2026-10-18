"""Compare PyTorch streaming reduced model vs C scalar output, block by block."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys
BASE=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR=BASE/"neural_reference"; BUD=BASE/"board_budget_20261005"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
import torch, numpy as np
from train_reduced_20261007 import build_net
from llvc_online_stream import LLVCAudioStream

net=build_net(NR/'LLVC/experiments/llvc/config_reduced.json')
ck=torch.load(BUD/'reduced_student_v2/final.pt',map_location='cpu',weights_only=True)
net.load_state_dict(ck['model'],strict=True); net.eval()
x=np.fromfile(BASE/"deploy_runtime/test/input.bin",dtype="<f4")
st=LLVCAudioStream(net)
parts=st.feed(x); parts+=st.finish()
ref=np.concatenate(parts)
c=np.fromfile(BASE/"deploy_runtime/out_pc_red.bin",dtype="<f4")
print("ref len",len(ref),"c len",len(c))
n=min(len(ref),len(c))
r=ref[:n]; cc=c[:n]
corr=np.corrcoef(r,cc)[0,1]
print("overall corr %.4f  ref rms %.4f c rms %.4f"%(corr,np.sqrt((r**2).mean()),np.sqrt((cc**2).mean())))
# per-block corr
for b in range(0,n,208):
    rb=r[b:b+208]; cb=cc[b:b+208]
    if len(rb)<208:break
    co=np.corrcoef(rb,cb)[0,1]
    print("block %3d corr %.4f refmax %.3f cmax %.3f"%(b//208,co,np.abs(rb).max(),np.abs(cb).max()))
