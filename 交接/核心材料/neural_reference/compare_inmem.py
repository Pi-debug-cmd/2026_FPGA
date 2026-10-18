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
t = BASE/"deploy_runtime"/"test"
enc, dec, outb = net.init_buffers(1, "cpu")
pre = net.convnet_pre.init_ctx_buf(1,"cpu")
front = torch.zeros(32)
pending = np.concatenate([np.empty(0, dtype=np.float32), bx])
nb = 0
c_before = np.fromfile(t/"enc3_before.bin", dtype=np.float32).reshape(13,512)
c_pwout = np.fromfile(t/"dbg_dcc3_pwout.bin", dtype=np.float32).reshape(13,512)
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
                dcell = encmod.dcc_layers[li]
                dwout = dcell.layers[0](dcc_in)
                lnout = dcell.layers[1](dwout)
                reluout = torch.relu(lnout)
                pwout = dcell.layers[3](reluout)
                # compare in memory
                ref_pw = pwout.permute(0,2,1).reshape(13,512).numpy()
                ref_din = reluout.permute(0,2,1).reshape(13,512).numpy()
                print("ref_din vs C_before maxdiff", float(np.abs(ref_din-c_before).max()))
                print("ref_pw vs C_pwout maxdiff", float(np.abs(ref_pw-c_pwout).max()))
                # run the same qd on c_before
                xc = torch.from_numpy(c_before).permute(1,0).unsqueeze(0)
                pw_c = dcell.layers[3](xc).permute(0,2,1).reshape(13,512).numpy()
                print("qd(C_before) vs C_pwout maxdiff", float(np.abs(pw_c-c_pwout).max()))
                print("ref_pw vs qd(C_before) maxdiff", float(np.abs(ref_pw-pw_c).max()))
            enc[...,s0:s1] = dcc_in[...,-encmod.buf_lengths[li]:]
            x = x + encmod.dcc_layers[li](dcc_in)
    front = shifted[-32:].clone()
    pending = pending[CHUNK:].copy()
    if nb == 4: break
