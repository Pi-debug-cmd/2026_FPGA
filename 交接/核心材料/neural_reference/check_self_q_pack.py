from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch, struct
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
net, _ = load_model(False)
ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
net.load_state_dict(ck["model"], strict=True); net.eval()
tl = "mask_gen.decoder.tf_dec_layers.0"
q_pt = net.state_dict()[f"{tl}.self_attn.in_proj_weight"][0:256].numpy()  # [256,256]

raw = open(BUD/"llvc_deploy_model.bin","rb").read()
scale_off = struct.unpack("<I", raw[36:40])[0]
packed_off = struct.unpack("<I", raw[40:44])[0]
mat_packed_off = np.frombuffer(raw[44+128*4:44+128*4+18*4], dtype=np.uint32)
mat_scale_off = np.frombuffer(raw[44+128*4+18*4:44+128*4+36*4], dtype=np.uint32)
mi = 8
poff = mat_packed_off[mi]; soff = mat_scale_off[mi]
packed = np.frombuffer(raw, dtype=np.uint8, count=256*512, offset=packed_off+poff).reshape(256,512)
sc = np.frombuffer(raw, dtype=np.float32, count=256, offset=scale_off+soff)
# packed[k,j] = Wq[j,k]; dequant
Wq = packed[:, :256].T.view(np.int8).astype(np.float32)  # [out=256,in=256]
Wdq = Wq * sc[:,None]
print("packed self_q dequant vs actual maxdiff:", np.abs(Wdq-q_pt).max())
print("sc first 3:", sc[:3])
