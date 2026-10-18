"""Export reduced student to a single binary for the C runtime (enc384/dec192)."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch, struct
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from build_reduced_bias_20261009 import build_net_bias as build_net

net = build_net(NR/"LLVC/experiments/llvc/config_reduced.json")
ck = torch.load(BUD/"reduced_student_bias_content_v1/final.pt", map_location="cpu", weights_only=True)
net.load_state_dict(ck["model"], strict=True); net.eval()
sd = net.state_dict()

floats = []
def add(name, arr):
    a = np.asarray(arr, dtype=np.float32).reshape(-1)
    floats.append((name, a)); return len(floats)-1

# convnet_pre (12 blocks)
for i in range(12):
    add(f"cn{i}.fw", sd[f"convnet_pre.down_convs.{i}.filter.weight"].numpy())
    add(f"cn{i}.fb", sd[f"convnet_pre.down_convs.{i}.filter.bias"].numpy())
    add(f"cn{i}.gw", sd[f"convnet_pre.down_convs.{i}.gate.weight"].numpy())
    add(f"cn{i}.gb", sd[f"convnet_pre.down_convs.{i}.gate.bias"].numpy())
add("in_conv.w", sd["in_conv.0.weight"].numpy())
# DCC per block (6)
for i in range(6):
    p = f"mask_gen.encoder.dcc_layers.dcc_{i}.layers"
    add(f"dcc{i}.dw", sd[f"{p}.0.weight"].numpy())
    add(f"dcc{i}.db", sd[f"{p}.0.bias"].numpy())
    add(f"dcc{i}.ln1w", sd[f"{p}.1.weight"].numpy())
    add(f"dcc{i}.ln1b", sd[f"{p}.1.bias"].numpy())
    add(f"dcc{i}.pb", sd[f"{p}.3.bias"].numpy())
    add(f"dcc{i}.ln2w", sd[f"{p}.4.weight"].numpy())
    add(f"dcc{i}.ln2b", sd[f"{p}.4.bias"].numpy())
# proj
add("proj_e2d_e.w", sd["mask_gen.proj_e2d_e.0.weight"].numpy())
add("proj_e2d_e.b", sd["mask_gen.proj_e2d_e.0.bias"].numpy())
add("proj_e2d_l.w", sd["mask_gen.proj_e2d_l.0.weight"].numpy())
add("proj_e2d_l.b", sd["mask_gen.proj_e2d_l.0.bias"].numpy())
add("proj_d2e.w", sd["mask_gen.proj_d2e.0.weight"].numpy())
add("proj_d2e.b", sd["mask_gen.proj_d2e.0.bias"].numpy())
# transformer
tl = "mask_gen.decoder.tf_dec_layers.0"
add("self.ipb", sd[f"{tl}.self_attn.in_proj_bias"].numpy())
add("self.ob", sd[f"{tl}.self_attn.out_proj.bias"].numpy())
add("cross.ipb", sd[f"{tl}.multihead_attn.in_proj_bias"].numpy())
add("cross.ob", sd[f"{tl}.multihead_attn.out_proj.bias"].numpy())
add("ffn1.b", sd[f"{tl}.linear1.bias"].numpy())
add("ffn2.b", sd[f"{tl}.linear2.bias"].numpy())
for n in ["norm1","norm2","norm3"]:
    add(f"{n}.w", sd[f"{tl}.{n}.weight"].numpy())
    add(f"{n}.b", sd[f"{tl}.{n}.bias"].numpy())
add("out_conv.w", sd["out_conv.0.weight"].numpy())
# label embedding constant
label = torch.zeros(1,1)
with torch.no_grad():
    lconst = net.label_embedding(label)[0].numpy()
add("label", lconst)
add("posenc_26", sd["mask_gen.decoder.pos_enc.pe"][0, :26, :].numpy())
add("timbre_bias", sd["timbre_bias"].numpy())

def quant_pack(weight):
    W = weight.detach()
    if W.dim() == 3: W = W.squeeze(-1)
    W = W.numpy().astype(np.float32)
    out_c, in_c = W.shape
    amax = np.max(np.abs(W), axis=1).clip(1e-8)
    sw = amax/127.0
    Wq = np.round(W/sw[:,None]).clip(-128,127).astype(np.int8)
    packed = np.zeros((in_c,512), dtype=np.uint8)
    packed[:, :out_c] = Wq.T.view(np.uint8)
    return packed.reshape(-1), sw.astype(np.float32)

# 16 matrices: 6 enc pointwise, 4 self attn, 4 cross attn, 2 ffn
mats = []
for i in range(6): mats.append((f"enc{i}",384,384,13))
for att in ["self","cross"]:
    mats.append((f"{att}_q",192,192,13))
    mats.append((f"{att}_k",192,192,26))
    mats.append((f"{att}_v",192,192,26))
    mats.append((f"{att}_o",192,192,13))
mats.append(("ffn1",384,192,13))
mats.append(("ffn2",192,384,13))
assert len(mats)==16

packed_list, scale_list, mat_desc = [], [], []
for name, oc, ic, fr in mats:
    if name.startswith("enc"):
        i = int(name[3:]); W = sd[f"mask_gen.encoder.dcc_layers.dcc_{i}.layers.3.weight"]
    elif name in ("self_q","self_k","self_v"):
        W = sd[f"{tl}.self_attn.in_proj_weight"][ {"q":0,"k":1,"v":2}[name[-1]]*192: ({"q":0,"k":1,"v":2}[name[-1]]+1)*192 ]
    elif name == "self_o":
        W = sd[f"{tl}.self_attn.out_proj.weight"]
    elif name in ("cross_q","cross_k","cross_v"):
        W = sd[f"{tl}.multihead_attn.in_proj_weight"][ {"q":0,"k":1,"v":2}[name[-1]]*192: ({"q":0,"k":1,"v":2}[name[-1]]+1)*192 ]
    elif name == "cross_o":
        W = sd[f"{tl}.multihead_attn.out_proj.weight"]
    elif name == "ffn1":
        W = sd[f"{tl}.linear1.weight"]
    elif name == "ffn2":
        W = sd[f"{tl}.linear2.weight"]
    pk, sc = quant_pack(W)
    mat_desc.append((name,oc,ic,fr)); packed_list.append(pk); scale_list.append(sc)

HDR=4096
float_blob=np.concatenate([a for _,a in floats]).astype(np.float32)
scale_blob=np.concatenate(scale_list).astype(np.float32)
packed_blob=np.concatenate(packed_list).astype(np.uint8)
float_off=HDR; scale_off=float_off+float_blob.nbytes; packed_off=scale_off+scale_blob.nbytes
float_arr_off=np.zeros(128,dtype=np.uint32); acc=0
for idx,(name,a) in enumerate(floats):
    float_arr_off[idx]=acc; acc+=a.nbytes
mat_packed_off=np.zeros(16,dtype=np.uint32); mat_scale_off=np.zeros(16,dtype=np.uint32)
accp=accs=0
for midx,(pk,sc) in enumerate(zip(packed_list,scale_list)):
    mat_packed_off[midx]=accp; mat_scale_off[midx]=accs
    accp+=pk.nbytes; accs+=sc.nbytes
header=struct.pack("<8I",0x4C4C5643,3,16,384,192,13,13,0)
header+=struct.pack("<3I",float_off,scale_off,packed_off)
header+=float_arr_off.astype("<u4").tobytes()
header+=mat_packed_off.astype("<u4").tobytes()
header+=mat_scale_off.astype("<u4").tobytes()
assert len(header)<HDR
model_path=BUD/"reduced_student_bias_content_v1/model_bias.bin"
with open(model_path,"wb") as f:
    f.write(header); f.write(b"\x00"*(HDR-len(header)))
    f.write(float_blob.tobytes()); f.write(scale_blob.tobytes()); f.write(packed_blob.tobytes())
print("WROTE",model_path,"size",model_path.stat().st_size)
print("float",float_blob.nbytes,"scale",scale_blob.nbytes,"packed",packed_blob.nbytes)
