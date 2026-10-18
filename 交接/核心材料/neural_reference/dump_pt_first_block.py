from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read

net, _ = load_model(False)
ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
net.load_state_dict(ck["model"], strict=True); net.eval()

B = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\fargan_v8_fullchain_verification\B_普通男声_同一句中文.wav")
bx = read(str(B))
L = 16
front = torch.zeros(2*L)
shifted = torch.from_numpy(bx[L:L+208].copy())
block = torch.cat((front, shifted)).reshape(1,1,-1)

def dumpCF(t, name):
    # t: [B, channel, frame] -> flat [frame, channel]
    t.permute(0,2,1).contiguous().numpy().reshape(-1).astype(np.float32).tofile(tdir/name)

tdir = BASE/"deploy_runtime"/"test"
with torch.inference_mode():
    pre = net.convnet_pre.init_ctx_buf(1, "cpu")
    convnet_out, pre = net.convnet_pre(block, pre)
    cn = block + convnet_out
    cn.numpy().reshape(-1).astype(np.float32).tofile(tdir/"pt_cn.bin")
    x = net.in_conv(cn)
    dumpCF(x, "pt_e_inconv.bin")
    enc_buf = net.mask_gen.encoder.init_ctx_buf(1, "cpu")
    e, enc_buf = net.mask_gen.encoder(x, enc_buf)
    dumpCF(e, "pt_e_dcc.bin")
    label = torch.zeros(1,1)
    l = net.label_embedding(label); l = l.unsqueeze(2)*e
    dumpCF(l, "pt_l.bin")
    em = net.mask_gen.proj_e2d_e(e)
    tm = net.mask_gen.proj_e2d_l(l)
    dumpCF(em, "pt_mem.bin")
    dumpCF(tm, "pt_tgt.bin")
    dec_buf = net.mask_gen.decoder.init_ctx_buf(1, "cpu")
    m, dec_buf = net.mask_gen.decoder(tm, em, dec_buf)
    m = net.mask_gen.proj_d2e(m)
    m = l + m
    out_buf = torch.zeros(1,512,4)
    xx = e*m
    outin = torch.cat((out_buf, xx), dim=-1)
    dumpCF(outin, "pt_outin.bin")
print("wrote corrected pt intermediates")
