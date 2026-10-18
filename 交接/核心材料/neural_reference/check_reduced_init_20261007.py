"""Quick forward sanity check of reduced init vs full stage3 on fixed sentence."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, ast, json, zipfile
BASE=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR=BASE/"neural_reference"; BUD=BASE/"board_budget_20261005"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
import torch, torch.nn as nn, math, numpy as np
import librosa
from train_board_student_20261005 import read

def build_net(config_path, ckpt):
    wheel=NR/'dependency_source_audit/speechbrain-0.5.16-py3-none-any.whl'
    with zipfile.ZipFile(wheel) as z:
        text=z.read('speechbrain/lobes/models/transformer/Transformer.py').decode()
    cls=next(n for n in ast.parse(text).body if isinstance(n,ast.ClassDef) and n.name=='PositionalEncoding')
    ns=dict(torch=torch,nn=nn,math=math,__name__='r')
    exec(compile(ast.Module(body=[cls],type_ignores=[]),'w','exec'),ns)
    t=ast.parse((NR/'LLVC/model.py').read_text())
    t.body=[n for n in t.body if not (isinstance(n,ast.ImportFrom) and n.module=='speechbrain.lobes.models.transformer.Transformer')]
    nspace=dict(PositionalEncoding=ns['PositionalEncoding'],__name__='llvc_n')
    exec(compile(t,str(NR/'LLVC/model.py'),'exec'),nspace)
    cfg=json.loads(Path(config_path).read_text())
    net=nspace['Net'](**cfg['model_params']).eval()
    sd=torch.load(ckpt,map_location='cpu',weights_only=True)['model']
    net.load_state_dict(sd,strict=True); return net

device='cuda'
FIXED=BUD/"fargan_v8_fullchain_verification/B_普通男声_同一句中文.wav"
x=torch.tensor(read(str(FIXED)),device=device)[None,None]
red=build_net(NR/'LLVC/experiments/llvc/config_reduced.json',
              BUD/'reduced_init/reduced_init.pt').to(device)
with torch.no_grad():
    o=red(x)[0,0].cpu().numpy()
print("red init rms %.4f flat %.5f"%(np.sqrt((o**2).mean()),
    float(np.median(librosa.feature.spectral_flatness(y=o,n_fft=1024,hop_length=160)))))
from differentiable_speaker_20261005 import FrozenSpeaker
spk=FrozenSpeaker().to(device).eval()
tgt=read(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav")
te=spk.embedding(torch.tensor(tgt,device=device))
print("red init cos %.4f"%float(torch.nn.functional.cosine_similarity(
    spk.embedding(torch.tensor(o,device=device)),te).item()))
