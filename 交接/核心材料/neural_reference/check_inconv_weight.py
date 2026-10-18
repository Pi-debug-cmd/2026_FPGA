from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, struct
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
import torch

# parse model binary
mb = BUD/"llvc_deploy_model.bin"
raw = open(mb,"rb").read()
magic, ver, L, enc, dec, chunk, ctx, pad = struct.unpack("<8I", raw[:32])
float_off, scale_off, packed_off = struct.unpack("<3I", raw[32:44])
float_arr_off = np.frombuffer(raw[44:44+128*4], dtype=np.uint32)
# extract in_conv weight at index 48: 512*48 = 24576 floats
off = float_arr_off[48]
w_bin = np.frombuffer(raw, dtype=np.float32, count=512*48,
                      offset=float_off+off).reshape(512,48)

net, _ = load_model(False)
ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
net.load_state_dict(ck["model"], strict=True); net.eval()
w_pt = net.in_conv[0].weight.detach().numpy().reshape(512,48)
print("weight maxdiff", np.abs(w_bin-w_pt).max())
print("w_bin[0,:5]", w_bin[0,:5])
print("w_pt [0,:5]", w_pt[0,:5])
