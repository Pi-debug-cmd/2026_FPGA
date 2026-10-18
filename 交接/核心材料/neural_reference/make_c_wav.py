import numpy as np, soundfile as sf
t = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test"
c = np.fromfile(t+r"\cout.bin", dtype=np.float32)
# clip to safe range
c = np.clip(c, -1, 1)
outdir = r"D:\总进度\C运行时试听_2026-10-06"
import os
os.makedirs(outdir, exist_ok=True)
sf.write(outdir+r"\C运行时输出.wav", c, 16000, subtype="PCM_16")
q = np.fromfile(t+r"\ref_quant_stream.bin", dtype=np.float32)
sf.write(outdir+r"\量化模型参考.wav", np.clip(q,-1,1), 16000, subtype="PCM_16")
f = np.fromfile(t+r"\ref_float_stream.bin", dtype=np.float32)
sf.write(outdir+r"\浮点模型参考.wav", np.clip(f,-1,1), 16000, subtype="PCM_16")
print("wrote 3 wavs to", outdir)
