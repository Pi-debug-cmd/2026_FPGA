from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read
from differentiable_speaker_20261005 import FrozenSpeaker
import quant_sim_20261006 as Q
import soundfile as sf

B = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\fargan_v8_fullchain_verification\B_普通男声_同一句中文.wav")
TREF = Path(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav")

# robust activation scale
def robust_act(pct):
    def fn(x):
        a = x.abs().flatten()
        if pct >= 100:
            amax = a.max()
        else:
            amax = torch.quantile(a, pct/100.0)
        amax = amax.clamp_min(1e-8)
        sx = amax/127.0
        xq = torch.clamp(torch.round(x/sx), -128, 127).to(torch.int8)
        return xq, float(sx)
    return fn

def build():
    net, cfg = load_model(False)
    ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
    net.load_state_dict(ck["model"], strict=True); net.eval()
    for i in range(8):
        cell = net.mask_gen.encoder.dcc_layers[i].layers[3]
        net.mask_gen.encoder.dcc_layers[i].layers[3] = Q.QuantizedDense(cell)
    layer = net.mask_gen.decoder.tf_dec_layers[0]
    layer.self_attn = Q.QuantizedMHA(layer.self_attn)
    layer.multihead_attn = Q.QuantizedMHA(layer.multihead_attn)
    layer.linear1 = Q.QuantizedDense(layer.linear1)
    layer.linear2 = Q.QuantizedDense(layer.linear2)
    return net

def run(net):
    bx = read(str(B))
    with torch.no_grad():
        return net(torch.tensor(bx)[None,None])[0,0].numpy()

ref = run(build(False)) if False else None
# baseline reference (float)
net0, _ = load_model(False)
ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
net0.load_state_dict(ck["model"], strict=True); net0.eval()
bx = read(str(B))
with torch.no_grad():
    ref = net0(torch.tensor(bx)[None,None])[0,0].numpy()

for pct in [100, 99.9, 99.5]:
    Q.quantize_activation = robust_act(pct)
    q = run(build())
    d = ref-q
    snr = 10*np.log10((ref**2).mean()/(d**2).mean())
    print(f"pct={pct}: SNR={snr:.2f}dB max|err|={np.abs(d).max():.4f}")
    if pct==100:
        sf.write(BUD/"quant_max.wav", q, 16000)
    if pct==99.9:
        sf.write(BUD/"quant_p999.wav", q, 16000)
