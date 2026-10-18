from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch, json
import torch.nn as nn
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"stage3_anchor_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read
from quant_sim_20261006 import QuantizedDense, QuantizedMHA
import soundfile as sf

B = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\fargan_v8_fullchain_verification\B_普通男声_同一句中文.wav")

def build(quantize):
    net, cfg = load_model(False)
    ck = torch.load(OUT/"checkpoint_step2000.pt", map_location="cpu", weights_only=True)
    net.load_state_dict(ck["model"], strict=True); net.eval()
    if quantize:
        # 8 encoder pointwise
        for i in range(8):
            cell = net.mask_gen.encoder.dcc_layers[i].layers[3]
            net.mask_gen.encoder.dcc_layers[i].layers[3] = QuantizedDense(cell)
        # 2 MHA
        layer = net.mask_gen.decoder.tf_dec_layers[0]
        layer.self_attn = QuantizedMHA(layer.self_attn)
        layer.multihead_attn = QuantizedMHA(layer.multihead_attn)
        # 2 FFN
        layer.linear1 = QuantizedDense(layer.linear1)
        layer.linear2 = QuantizedDense(layer.linear2)
    return net

def run(net, device):
    net = net.to(device)
    bx = read(str(B))
    with torch.no_grad():
        so = net(torch.tensor(bx, device=device)[None,None])[0,0].cpu().numpy()
    return so

ref = run(build(False), "cpu")
quant = run(build(True), "cpu")
n = min(len(ref), len(quant))
d = ref[:n]-quant[:n]
sig_pow = (ref[:n]**2).mean()
snr = 10*np.log10(sig_pow/(d**2).mean())
print(f"FULL DENSE W8A8: max|err|={np.abs(d).max():.5f} rmse={np.sqrt((d**2).mean()):.5f} SNR={snr:.2f}dB")
sf.write(BUD/"quant_full_dense_output.wav", quant, 16000)
print("WROTE quant_full_dense_output.wav")

# pitch and target cos
import librosa
def pitch(x):
    f0,_,_ = librosa.pyin(x, fmin=60, fmax=500, sr=16000); f0=f0[~np.isnan(f0)]
    return float(np.median(f0))
print("ref f0", round(pitch(ref),1), "quant f0", round(pitch(quant),1))
