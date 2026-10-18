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

B = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\fargan_v8_fullchain_verification\B_普通男声_同一句中文.wav")
net, _ = load_model(False)
ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
net.load_state_dict(ck["model"], strict=True); net.eval()

bx = read(str(B))
# offline full (pad=True default)
with torch.no_grad():
    off = net(torch.tensor(bx)[None,None])[0,0].numpy()
print("offline len", len(off))

# streaming
st = LLVCAudioStream(net)
parts = st.feed(bx)
parts += st.finish()
stream = np.concatenate(parts)
print("stream len", len(stream))
n = min(len(off), len(stream))
d = off[:n]-stream[:n]
snr = 10*np.log10((off[:n]**2).mean()/(d**2).mean())
print(f"offline vs LLVCAudioStream: SNR={snr:.3f}dB maxdiff={np.abs(d).max():.5f}")
