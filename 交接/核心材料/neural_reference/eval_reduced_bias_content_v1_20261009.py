"""Offline screening of same-architecture reduced student v3 against deployed v2."""
from pathlib import Path
import sys, json
import numpy as np
import torch
import torch.nn.functional as F
import librosa
import soundfile as sf

BASE=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR=BASE/"neural_reference"; BUD=BASE/"board_budget_20261005"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
from build_reduced_bias_20261009 import build_net_bias as build_net
from differentiable_speaker_20261005 import FrozenSpeaker
from train_board_student_20261005 import read
from llvc_online_stream import LLVCAudioStream

config=NR/"LLVC/experiments/llvc/config_reduced.json"
device="cuda"
def load(path):
    net=build_net(config).to(device).eval()
    missing,unexpected=net.load_state_dict(torch.load(path,map_location="cpu",weights_only=True)["model"],strict=False)
    assert not unexpected and (not missing or missing==["timbre_bias"]),(missing,unexpected)
    return net
nets={
    "deployed_v2":load(BUD/"reduced_student_v2/final.pt"),
    "bias_content_step400":load(BUD/"reduced_student_bias_content_v1/checkpoint_step400.pt"),
    "bias_content_step800":load(BUD/"reduced_student_bias_content_v1/final.pt")
}
spk=FrozenSpeaker().to(device).eval()
target=read(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav")
with torch.inference_mode():
    te=spk.embedding(torch.tensor(target,device=device))
def cos(x):
    with torch.inference_mode():
        e=spk.embedding(torch.tensor(x,device=device))
        return float(F.cosine_similarity(e,te).item())
def mel(y):
    m=librosa.feature.melspectrogram(y=y,sr=16000,n_fft=1024,hop_length=160,n_mels=80,power=1.0)
    return np.log1p(m)
def stats(x,t):
    return dict(cos=cos(x),mel_to_teacher=float(np.mean(np.abs(mel(x)-mel(t)))),rms=float(np.sqrt(np.mean(x*x))),peak=float(np.max(np.abs(x))))
def infer(net,x):
    stream=LLVCAudioStream(net)
    parts=stream.feed(x);parts+=stream.finish()
    return np.concatenate(parts)
manifest=json.loads((BUD/"full_train_corpus_16k/manifest.json").read_text(encoding="utf-8"))
rows=[]
outdir=BUD/"reduced_student_bias_content_v1/screen";outdir.mkdir(exist_ok=True)
for e in manifest["validation"][:4]:
    x=np.fromfile(e["src"],dtype="<f4");t=np.fromfile(e["tch"],dtype="<f4")
    row=dict(stem=e["stem"],source=stats(x,t),teacher=stats(t,t))
    for name,net in nets.items():
        y=infer(net,x)
        row[name]=stats(y,t)
        sf.write(outdir/(e["stem"]+"_"+name+".wav"),y,16000)
    rows.append(row)
    print(json.dumps(row,ensure_ascii=False),flush=True)
fixed=read(str(BUD/"fargan_v8_fullchain_verification/B_普通男声_同一句中文.wav"))
for name,net in nets.items():
    y=infer(net,fixed)
    sf.write(outdir/("fixed_"+name+".wav"),y,16000)
    print("fixed",name,"cos",cos(y),"rms",float(np.sqrt(np.mean(y*y))),flush=True)
summary={}
for name in nets:
    summary[name]={
      "mean_cos":float(np.mean([r[name]["cos"] for r in rows])),
      "mean_mel_to_teacher":float(np.mean([r[name]["mel_to_teacher"] for r in rows]))
    }
print("SUMMARY",json.dumps(summary,ensure_ascii=False),flush=True)
(outdir/"screen.json").write_text(json.dumps(dict(rows=rows,summary=summary),ensure_ascii=False,indent=2),encoding="utf-8")





