from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from llvc_online_stream import LLVCAudioStream
import quant_sim_20261006 as Q

def make_net(quant):
    net, _ = load_model(False)
    ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
    net.load_state_dict(ck["model"], strict=True); net.eval()
    if quant:
        for i in range(8):
            cell = net.mask_gen.encoder.dcc_layers[i].layers[3]
            net.mask_gen.encoder.dcc_layers[i].layers[3] = Q.QuantizedDense(cell)
        layer = net.mask_gen.decoder.tf_dec_layers[0]
        layer.self_attn = Q.QuantizedMHA(layer.self_attn)
        layer.multihead_attn = Q.QuantizedMHA(layer.multihead_attn)
        layer.linear1 = Q.QuantizedDense(layer.linear1)
        layer.linear2 = Q.QuantizedDense(layer.linear2)
    return net

bx = np.fromfile(BASE/"deploy_runtime"/"test"/"input.bin", dtype=np.float32)
t = BASE/"deploy_runtime"/"test"

# float stream
nf = make_net(False)
st = LLVCAudioStream(nf); p = st.feed(bx); p += st.finish()
fstream = np.concatenate(p)
print("float stream len", len(fstream))

# quant stream
nq = make_net(True)
st = LLVCAudioStream(nq); p = st.feed(bx); p += st.finish()
qstream = np.concatenate(p)
print("quant stream len", len(qstream))

# C output
c = np.fromfile(t/"cout.bin", dtype=np.float32)
n = min(len(fstream), len(qstream), len(c))
fstream=fstream[:n]; qstream=qstream[:n]; c=c[:n]

def snr(a,b):
    e=a-b
    return 10*np.log10(np.mean(a**2)/np.mean(e**2))

print("float vs quant SNR %.2f dB" % snr(fstream, qstream))
print("C vs quant SNR %.2f dB" % snr(c, qstream))
print("C vs float SNR %.2f dB" % snr(c, fstream))
# save
fstream.astype(np.float32).tofile(t/"ref_float_stream.bin")
qstream.astype(np.float32).tofile(t/"ref_quant_stream.bin")
