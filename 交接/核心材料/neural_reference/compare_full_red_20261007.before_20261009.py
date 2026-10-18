"""Compare C vs PyTorch streaming AND non-streaming: corr, flat, cos on this input."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys
BASE=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR=BASE/"neural_reference"; BUD=BASE/"board_budget_20261005"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
import torch, numpy as np, librosa
from train_reduced_20261007 import build_net
from llvc_online_stream import LLVCAudioStream
import torch.nn.functional as F
from differentiable_speaker_20261005 import FrozenSpeaker
from train_board_student_20261005 import read

net=build_net(NR/'LLVC/experiments/llvc/config_reduced.json')
ck=torch.load(BUD/'reduced_student_v2/final.pt',map_location='cpu',weights_only=True)
net.load_state_dict(ck['model'],strict=True); net.eval()
x=np.fromfile(BASE/"deploy_runtime/test/input.bin",dtype="<f4")
st=LLVCAudioStream(net)
parts=st.feed(x); parts+=st.finish()
ref=np.concatenate(parts)
c=np.fromfile(BASE/"deploy_runtime/out_pc_red.bin",dtype="<f4")
# non-streaming
with torch.inference_mode():
    ns=net(torch.tensor(x)[None,None])[0,0].numpy()
spk=FrozenSpeaker().to("cuda").eval()
tgt_emb=spk.embedding(torch.tensor(read(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav"),device="cuda"))
def cos(w):
    e=spk.embedding(torch.tensor(w,device="cuda"))
    return float(F.cosine_similarity(e,tgt_emb))
def flat(w): return float(np.median(librosa.feature.spectral_flatness(y=w,n_fft=1024,hop_length=160)))
for name,w in [("C",c),("stream_ref",ref),("nonstream",ns)]:
    print("%-11s rms %.4f flat %.4f cos %.4f"%(name,np.sqrt((w**2).mean()),flat(w),cos(w)))
# write wavs
import soundfile as sf
OUT=Path(r"D:\总进度\缩减模型C试听_20261007"); OUT.mkdir(exist_ok=True)
sf.write(OUT/"C输出.wav",c,16000)
sf.write(OUT/"PyTorch流式参考.wav",ref,16000)
sf.write(OUT/"原始输入.wav",x,16000)
print("wrote",OUT)
