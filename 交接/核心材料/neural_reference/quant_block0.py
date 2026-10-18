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
layer = net.mask_gen.decoder.tf_dec_layers[0]
layer.self_attn = Q.QuantizedMHA(layer.self_attn)
layer.multihead_attn = Q.QuantizedMHA(layer.multihead_attn)
layer.linear1 = Q.QuantizedDense(layer.linear1)
layer.linear2 = Q.QuantizedDense(layer.linear2)

B = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\fargan_v8_fullchain_verification\B_普通男声_同一句中文.wav")
bx = read(str(B)); L=16
front = torch.zeros(2*L); shifted = torch.from_numpy(bx[L:L+208].copy())
block = torch.cat((front, shifted)).reshape(1,1,-1)
tdir = BASE/"deploy_runtime"/"test"
enc, dec, out = net.init_buffers(1, "cpu")
pre = net.convnet_pre.init_ctx_buf(1,"cpu")
with torch.inference_mode():
    speech, enc, dec, out, pre = net(block, enc, dec, out, pre, pad=False)
y = speech.numpy().reshape(-1)
print("quant pytorch block0 output maxabs:", np.abs(y).max())
print("first 10:", y[:10])
y.astype(np.float32).tofile(tdir/"q_block0_out.bin")
