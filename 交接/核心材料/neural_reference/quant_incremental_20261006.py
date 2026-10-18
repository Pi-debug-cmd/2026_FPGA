from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read
from quant_sim_20261006 import QuantizedDense, QuantizedMHA

B = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\fargan_v8_fullchain_verification\B_普通男声_同一句中文.wav")

def build(enc, mha, ffn):
    net, cfg = load_model(False)
    ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
    net.load_state_dict(ck["model"], strict=True); net.eval()
    if enc:
        for i in range(8):
            cell = net.mask_gen.encoder.dcc_layers[i].layers[3]
            net.mask_gen.encoder.dcc_layers[i].layers[3] = QuantizedDense(cell)
    layer = net.mask_gen.decoder.tf_dec_layers[0]
    if mha:
        layer.self_attn = QuantizedMHA(layer.self_attn)
        layer.multihead_attn = QuantizedMHA(layer.multihead_attn)
    if ffn:
        layer.linear1 = QuantizedDense(layer.linear1)
        layer.linear2 = QuantizedDense(layer.linear2)
    return net

def run(net):
    bx = read(str(B))
    with torch.no_grad():
        return net(torch.tensor(bx)[None,None])[0,0].numpy()

ref = run(build(False,False,False))
for name, (e,m,f) in [("enc",(True,False,False)),
                      ("enc+ffn",(True,False,True)),
                      ("enc+mha",(True,True,False)),
                      ("enc+mha+ffn",(True,True,True))]:
    q = run(build(e,m,f))
    d = ref-q
    snr = 10*np.log10((ref**2).mean()/(d**2).mean())
    print(f"{name:14s} SNR={snr:6.2f}dB  max|err|={np.abs(d).max():.4f}")
