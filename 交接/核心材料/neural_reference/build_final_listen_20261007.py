"""Build final listening package: held-out conversions from stage2 checkpoint."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, json
import numpy as np, torch
import librosa, soundfile as sf
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"
CORPUS = BUD/"full_train_corpus_16k"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read

OUT=Path(r"D:\总进度\最终学生试听v2_20261007"); OUT.mkdir(parents=True,exist_ok=True)
CKPT=BUD/"stage3_anchor_student/checkpoint_step2000.pt"
m=json.loads((CORPUS/"manifest.json").read_text(encoding="utf-8"))
net,cfg=load_model(False)
net.load_state_dict(torch.load(CKPT,map_location="cpu",weights_only=True)["model"],strict=True)
net=net.to("cuda").eval()

# fixed sentence
fx=BUD/"fargan_v8_fullchain_verification/B_普通男声_同一句中文.wav"
with torch.no_grad():
    o=net(torch.tensor(read(str(fx)),device="cuda")[None,None])[0,0].cpu().numpy()
sf.write(OUT/"3_学生转换_固定句.wav",o,16000)
# 4 held-out validation conversions
for i,e in enumerate(m["validation"][:4]):
    src=np.fromfile(e["src"],dtype="<f4")
    with torch.no_grad():
        o=net(torch.tensor(src,device="cuda")[None,None])[0,0].cpu().numpy()
    sf.write(OUT/("学生_heldout%d_%s.wav"%(i+1,e["stem"])),o,16000)
    sf.write(OUT/("教师_heldout%d_%s.wav"%(i+1,e["stem"])),np.fromfile(e["tch"],dtype="<f4"),16000)
print("done")
