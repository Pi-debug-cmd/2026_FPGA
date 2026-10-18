from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read
from llvc_online_stream import LLVCAudioStream
import quant_sim_20261006 as Q

# Build a model with quantized dense layers (mirrors the C reference backend).
net, _ = load_model(False)
ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
net.load_state_dict(ck["model"], strict=True); net.eval()
# The encoder is net.mask_gen.encoder; dcc_layers is nn.Sequential
for i in range(8):
    cell = net.mask_gen.encoder.dcc_layers[i].layers[3]
    net.mask_gen.encoder.dcc_layers[i].layers[3] = Q.QuantizedDense(cell)
layer = net.mask_gen.decoder.tf_dec_layers[0]
layer.self_attn = Q.QuantizedMHA(layer.self_attn)
layer.multihead_attn = Q.QuantizedMHA(layer.multihead_attn)
layer.linear1 = Q.QuantizedDense(layer.linear1)
layer.linear2 = Q.QuantizedDense(layer.linear2)

B = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\fargan_v8_fullchain_verification\B_普通男声_同一句中文.wav")
bx = read(str(B))
st = LLVCAudioStream(net)
parts = st.feed(bx); parts += st.finish()
qstream = np.concatenate(parts)
print("qstream len", len(qstream))

# write test files
tdir = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test")
tdir.mkdir(parents=True, exist_ok=True)
bx.astype(np.float32).tofile(tdir/"input.bin")
qstream.astype(np.float32).tofile(tdir/"ref_quant_stream.bin")
print("wrote input.bin and ref_quant_stream.bin")
