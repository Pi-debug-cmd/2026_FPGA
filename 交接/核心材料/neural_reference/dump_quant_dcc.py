from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read
import quant_sim_20261006 as Q

net, _ = load_model(False)
ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
net.load_state_dict(ck["model"], strict=True); net.eval()
for i in range(8):
    cell = net.mask_gen.encoder.dcc_layers[i].layers[3]
    net.mask_gen.encoder.dcc_layers[i].layers[3] = Q.QuantizedDense(cell)

B = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\fargan_v8_fullchain_verification\B_普通男声_同一句中文.wav")
bx = read(str(B)); L=16
front = torch.zeros(2*L); shifted = torch.from_numpy(bx[L:L+208].copy())
block = torch.cat((front, shifted)).reshape(1,1,-1)
tdir = BASE/"deploy_runtime"/"test"
def dumpCF(t, name):
    t.permute(0,2,1).contiguous().numpy().reshape(-1).astype(np.float32).tofile(tdir/name)
with torch.inference_mode():
    pre = net.convnet_pre.init_ctx_buf(1,"cpu")
    cnv, pre = net.convnet_pre(block, pre)
    cn = block + cnv
    x = net.in_conv(cn)
    enc = net.mask_gen.encoder
    ctx_buf = enc.init_ctx_buf(1,"cpu")
    for i in range(8):
        s0 = enc.buf_indices[i]; s1 = s0+enc.buf_lengths[i]
        dcc_in = torch.cat((ctx_buf[...,s0:s1], x), dim=-1)
        ctx_buf[...,s0:s1] = dcc_in[...,-enc.buf_lengths[i]:]
        x = x + enc.dcc_layers[i](dcc_in)
        dumpCF(x, f"q_e_dcc_{i}.bin")
print("wrote quantized DCC e")
