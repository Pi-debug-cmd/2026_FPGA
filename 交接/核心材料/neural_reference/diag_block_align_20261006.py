from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read

net, _ = load_model(False)
ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
net.load_state_dict(ck["model"], strict=True); net.eval()
bx = read(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\fargan_v8_fullchain_verification\B_普通男声_同一句中文.wav")

# Replicate the streaming block 0 and run model(pad=False); compare block output
# to offline slices to find the alignment.
front = torch.zeros(32)
pending = bx.copy()
shifted = pending[16:224]
block = torch.cat([front, torch.tensor(shifted)])
# init buffers
enc, dec, outb = net.init_buffers(1, "cpu")
pre = net.convnet_pre.init_ctx_buf(1, "cpu")
with torch.no_grad():
    sp, enc, dec, outb, pre = net(block.reshape(1,1,-1), enc, dec, outb, pre, pad=False)
print("block0 out len", sp.shape[-1])
# offline full
with torch.no_grad():
    off = net(torch.tensor(bx)[None,None])[0,0].numpy()
bo = sp[0,0].numpy()
for off_try in [0,16,32]:
    d = bo[off_try:off_try+len(bo)] - off[:len(bo)-off_try] if False else None
# Compare bo to off[0..207]
d0 = bo - off[:208]
print("bo vs off[0:208]: maxdiff", np.abs(d0).max())
d1 = bo - off[16:224]
print("bo vs off[16:224]: maxdiff", np.abs(d1).max())
