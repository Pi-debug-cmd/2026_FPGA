"""Comprehensive evaluation of the final full-size target student.

For the fixed campus sentence: pitch f0 (median) and target cosine for the
target A, source B, teacher CV3 C, and the student output. Also measure the
teacher's own target cosine (the ceiling).
"""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, json
import numpy as np
import torch
import torch.nn.functional as F

BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"
OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read
from differentiable_speaker_20261005 import FrozenSpeaker
import librosa, soundfile as sf

A = Path(r"D:\总进度\目标人物分析\原台词_模型直接转换检查_2026-10-04\A_目标人物原声.wav")
B = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\fargan_v8_fullchain_verification\B_普通男声_同一句中文.wav")
C = Path(r"D:\总进度\目标人物分析\原台词_模型直接转换检查_2026-10-04\C_新直接转换结果.wav")
TARGET_REF = Path(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav")

def pitch(path_or_arr):
    if isinstance(path_or_arr, Path):
        x, _ = librosa.load(path_or_arr, sr=16000)
    else:
        x = path_or_arr
    f0, vf, _ = librosa.pyin(x, fmin=60, fmax=500, sr=16000)
    f0 = f0[~np.isnan(f0)]
    return float(np.median(f0)), float(np.percentile(f0,10)), float(np.percentile(f0,90))

def main():
    device = "cuda"
    net, cfg = load_model(False)
    ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
    net.load_state_dict(ck["model"], strict=True); net = net.to(device).eval()

    speaker = FrozenSpeaker().to(device).eval()
    with torch.no_grad():
        ref_emb = speaker.embedding(torch.tensor(read(str(TARGET_REF)), device=device))

    def cos(p):
        x = torch.tensor(read(str(p)), device=device)
        with torch.no_grad(): return float((speaker.embedding(x[None])*ref_emb).sum())

    # student output (bulk)
    bx = read(str(B))
    with torch.no_grad():
        so = net(torch.tensor(bx, device=device)[None,None])[0,0].cpu().numpy()
    sf.write(OUT/"student_fixed_sentence_step3000.wav", so, 16000)
    with torch.no_grad():
        student_cos = float((speaker.embedding(torch.tensor(so,device=device)[None])*ref_emb).sum())

    res = {}
    for name, p in [("A_target", A), ("B_source", B), ("C_teacher", C)]:
        m, p10, p90 = pitch(p); res[name] = dict(f0=round(m,1), p10=round(p10,1), p90=round(p90,1),
                                                 target_cos=round(cos(p),3))
    sm, sp10, sp90 = pitch(so)
    res["student"] = dict(f0=round(sm,1), p10=round(sp10,1), p90=round(sp90,1),
                         target_cos=round(student_cos,3))
    res["parameters"] = sum(p.numel() for p in net.parameters())
    (OUT/"final_evaluation.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))

if __name__=="__main__":
    main()
