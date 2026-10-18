from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR))
from load_llvc_audit_model import load_model
import quant_sim_20261006 as Q

net, _ = load_model(False)
ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
net.load_state_dict(ck["model"], strict=True); net.eval()
for i in range(8):
    cell = net.mask_gen.encoder.dcc_layers[i].layers[3]
    net.mask_gen.encoder.dcc_layers[i].layers[3] = Q.QuantizedDense(cell)

bx = np.fromfile(BASE/"deploy_runtime"/"test"/"input.bin", dtype=np.float32)
L=16; CHUNK=208
tdir = BASE/"deploy_runtime"/"test"
def dumpCF(t, name):
    t.permute(0,2,1).contiguous().numpy().reshape(-1).astype(np.float32).tofile(tdir/name)

enc, dec, outb = net.init_buffers(1, "cpu")
pre = net.convnet_pre.init_ctx_buf(1,"cpu")
front = torch.zeros(32)
pending = np.concatenate([np.empty(0, dtype=np.float32), bx])
nb = 0
while len(pending) >= CHUNK+L:
    shifted = torch.from_numpy(pending[L:L+CHUNK].copy())
    block = torch.cat((front, shifted)).reshape(1,1,-1)
    nb += 1
    with torch.inference_mode():
        cnv, pre = net.convnet_pre(block, pre)
        cn = block + cnv
        x = net.in_conv(cn)
        encmod = net.mask_gen.encoder
        for li in range(8):
            s0 = encmod.buf_indices[li]; s1 = s0 + encmod.buf_lengths[li]
            dcc_in = torch.cat((enc[...,s0:s1], x), dim=-1)
            if nb == 4 and li == 3:
                # dump the raw din (context+current) before depthwise
                dumpCF(dcc_in, "ref_din3.bin")
                dcell = encmod.dcc_layers[li]
                # depthwise output (raw conv, before layernorm)
                dwout = dcell.layers[0](dcc_in)
                dumpCF(dwout, "ref_dcc3_dw.bin")
                # depthwise->layernorm->relu = dense input
                lnout = dcell.layers[1](dwout)
                reluout = torch.relu(lnout)
                dumpCF(reluout, "ref_dcc3_densein.bin")
                # raw pointwise dense output (QuantizedDense)
                qdcell = dcell.layers[3]
                xq_d, sx_d = Q.quantize_activation(reluout)
                # manually compute i8mm
                B,C,T = reluout.shape
                xq2 = xq_d.permute(0,2,1).reshape(B*T,C)
                yq_manual = torch.matmul(xq2.to(torch.int32), qdcell.wq.t().to(torch.int32))
                y_manual = yq_manual.float().reshape(B,T,-1).permute(0,2,1)
                y_manual = y_manual*(float(sx_d)*qdcell.sw).view(1,-1,1)
                if qdcell.bias is not None:
                    y_manual = y_manual + qdcell.bias.view(1,-1,1)
                pwout = qdcell(reluout)
                print("manual vs qd forward maxdiff", float((y_manual-pwout).abs().max()))
                print("if-block sx_d", float(sx_d))
                dumpCF(pwout, "ref_dcc3_pwout.bin")
                # second layernorm + relu
                ln2out = dcell.layers[4](pwout)
                ln2relu = torch.relu(ln2out)
                dumpCF(ln2relu, "ref_dcc3_ln2.bin")
            enc[...,s0:s1] = dcc_in[...,-encmod.buf_lengths[li]:]
            x = x + encmod.dcc_layers[li](dcc_in)
            if nb == 4:
                dumpCF(x, "ref_edcc_%d.bin"%li)
    front = shifted[-32:].clone()
    pending = pending[CHUNK:].copy()
    if nb == 4:
        print("done to block4")
        break




