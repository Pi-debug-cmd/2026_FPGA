from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch, soundfile as sf
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read

B = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\fargan_v8_fullchain_verification\B_普通男声_同一句中文.wav")

def run(device):
    net, cfg = load_model(False)
    ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
    net.load_state_dict(ck["model"], strict=True); net = net.to(device).eval()
    bx = read(str(B))
    with torch.no_grad():
        so = net(torch.tensor(bx, device=device)[None,None])[0,0].cpu().numpy()
    return so

saved = sf.read(OUT/"student_fixed_sentence_step3000.wav")[0]
for dev in ["cuda", "cpu"]:
    so = run(dev)
    n = min(len(so), len(saved))
    d = np.abs(so[:n]-saved[:n])
    print(f"{dev}: len={len(so)} saved={len(saved)} maxdiff={d.max():.5f} mean={d.mean():.5f}")
