import numpy as np, librosa, sys, torch
sys.path.insert(0, r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\neural_reference")
from differentiable_speaker_20261005 import FrozenSpeaker
t = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test"
spk = FrozenSpeaker().eval()
tgt_wave, _ = librosa.load(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav", sr=16000)
tgt_emb = spk.embedding(torch.tensor(tgt_wave))
def metrics(path, name):
    y, sr = librosa.load(path, sr=16000)
    f0, vf, _ = librosa.pyin(y, fmin=60, fmax=400, sr=16000)
    f0v = f0[~np.isnan(f0)]
    med = np.median(f0v); p10=np.percentile(f0v,10); p90=np.percentile(f0v,90)
    emb = spk.embedding(torch.tensor(y))
    cos = float(torch.nn.functional.cosine_similarity(emb, tgt_emb))
    print("%s: f0 %.1f p10 %.1f p90 %.1f cos %.3f" % (name, med, p10, p90, cos))
outdir = r"D:\总进度\C运行时试听_2026-10-06"
metrics(outdir+r"\C运行时输出.wav", "C运行时")
metrics(outdir+r"\量化模型参考.wav", "量化模型")
metrics(outdir+r"\浮点模型参考.wav", "浮点模型")
