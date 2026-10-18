"""One-block debug: compare C first-block vs PyTorch first-block (front=zeros)."""
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
x=np.fromfile(BASE/"deploy_runtime/test/input.bin",dtype="<f4")
# feed 224 samples via streaming (first block, front=zeros)
from llvc_online_stream import LLVCAudioStream
st=LLVCAudioStream(net)
# use a loud region: feed 224 from index 4480
chunk=x[4480:4480+224]
parts=st.feed(chunk)
ref=parts[0] if parts else np.zeros(208)
chunk.astype(np.float32).tofile(BASE/"deploy_runtime/test/one_loud_in.bin")
ref.astype(np.float32).tofile(BASE/"deploy_runtime/test/one_loud_ref.bin")
print("one-block ref rms %.4f max %.4f"%(np.sqrt((ref**2).mean()),np.abs(ref).max()))
print("ref[:16]",np.round(ref[:16],4))
