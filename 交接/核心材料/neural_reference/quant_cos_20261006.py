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

B = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\fargan_v8_fullchain_verification\B_普通男声_同一句中文.wav")
TREF = Path(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav")

def build(enc, mha, ffn):
    net, _ = load_model(False)
    ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
    net.load_state_dict(ck["model"], strict=True); net.eval()
    if enc:
        for i in range(8):
            c = net.mask_gen.encoder.dcc_layers[i].layers[3]
            net.mask_gen.encoder.dcc_layers[i].layers[3] = Q.QuantizedDense(c)
    layer = net.mask_gen.decoder.tf_dec_layers[0]
    if mha:
        layer.self_attn = Q.QuantizedMHA(layer.self_attn)
        layer.multihead_attn = Q.QuantizedMHA(layer.multihead_attn)
    if ffn:
        layer.linear1 = Q.QuantizedDense(layer.linear1)
        layer.linear2 = Q.QuantizedDense(layer.linear2)
    return net

def run(net):
    bx = read(str(B))
    with torch.no_grad():
        return net(torch.tensor(bx)[None,None])[0,0].numpy()

speaker = FrozenSpeaker().eval()
with torch.no_grad():
    ref_emb = speaker.embedding(torch.tensor(read(str(TREF)))[None])
def cos(x):
    with torch.no_grad():
        return float((speaker.embedding(torch.tensor(x)[None])*ref_emb).sum())

import soundfile as sf
configs = [("float", (False,False,False)),
           ("enc", (True,False,False)),
           ("enc+mha", (True,True,False)),
           ("all", (True,True,True))]
for name, flags in configs:
    q = run(build(*flags))
    print(f"{name:10s} target_cos={cos(q):.3f}")
    sf.write(BUD/f"qcos_{name}.wav", q, 16000)
