from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read
import quant_sim_20261006 as Q

net, _ = load_model(False)
ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
net.load_state_dict(ck["model"], strict=True); net.eval()
for i in range(8):
    cell = net.mask_gen.encoder.dcc_layers[i].layers[3]
    net.mask_gen.encoder.dcc_layers[i].layers[3] = Q.QuantizedDense(cell)
dec = net.mask_gen.decoder
layer = dec.tf_dec_layers[0]
qmha_self = Q.QuantizedMHA(layer.self_attn)
qmha_cross = Q.QuantizedMHA(layer.multihead_attn)
qd1 = Q.QuantizedDense(layer.linear1)
qd2 = Q.QuantizedDense(layer.linear2)

B = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\fargan_v8_fullchain_verification\B_普通男声_同一句中文.wav")
bx = read(str(B)); L=16
front = torch.zeros(2*L); shifted = torch.from_numpy(bx[L:L+208].copy())
block = torch.cat((front, shifted)).reshape(1,1,-1)
tdir = BASE/"deploy_runtime"/"test"
def dumpCF(t, name):
    # t [B,C,T] or [B,T,C]; write flat [frame,channel]
    if t.dim()==3 and t.shape[0]==1:
        if t.shape[1] in (256,512): t=t.permute(0,2,1)
    t.contiguous().numpy().reshape(-1).astype(np.float32).tofile(tdir/name)

with torch.inference_mode():
    enc_buf, dec_buf, out_buf = net.init_buffers(1, "cpu")
    pre = net.convnet_pre.init_ctx_buf(1,"cpu")
    cnv, pre = net.convnet_pre(block, pre)
    cn = block + cnv
    x = net.in_conv(cn)
    e, enc_buf = net.mask_gen.encoder(x, enc_buf)
    label = torch.zeros(1,1)
    l = net.label_embedding(label).unsqueeze(2)*e
    em13 = net.mask_gen.proj_e2d_e(e)
    tm13 = net.mask_gen.proj_e2d_l(l)
    # replicate C: prepend 13 context (from dec_buf) -> 26
    mem26 = torch.cat((dec_buf[:,0,:,:], em13.permute(0,2,1)), dim=1)
    tgt26 = torch.cat((dec_buf[:,1,:,:], tm13.permute(0,2,1)), dim=1)
    # speechbrain PE on the 26-window (matches C add_posenc)
    mem26 = mem26 + dec.pos_enc(mem26)
    tgt26 = tgt26 + dec.pos_enc(tgt26)
    dumpCF(tgt26, "q_tgt26.bin"); dumpCF(mem26, "q_mem26.bin")
    # self attention
    q_in = tgt26[:,-13:,:]
    dumpCF(q_in, "q_qin.bin"); dumpCF(tgt26, "q_kvin.bin")
    # dump Q/K/V projections (matches C dense calls)
    Qp = qmha_self._proj(q_in, "q"); Kp = qmha_self._proj(tgt26, "k"); Vp = qmha_self._proj(tgt26, "v")
    dumpCF(Qp, "q_sq.bin"); dumpCF(Kp, "q_sk.bin"); dumpCF(Vp, "q_sv.bin")
    sa, _ = qmha_self(q_in, tgt26, tgt26)
    dumpCF(sa, "q_dec_self.bin")
    qn = layer.norm1(q_in + sa)
    dumpCF(qn, "q_q_norm.bin")
    # cross attention
    ca, _ = qmha_cross(qn, mem26, mem26)
    dumpCF(ca, "q_dec_cross.bin")
    kvn = layer.norm2(qn + ca)
    dumpCF(kvn, "q_kv_norm.bin")
    # FFN (linear1/linear2 are nn.Linear on [B,T,C])
    h = qd1(kvn)
    h = torch.relu(h)
    f2 = qd2(h)
    fn = layer.norm3(kvn + f2)
    dumpCF(fn, "q_ffn_norm.bin")
print("wrote manual quant decoder dumps")
