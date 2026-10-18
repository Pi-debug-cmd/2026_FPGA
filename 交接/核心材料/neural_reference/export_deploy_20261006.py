"""Export the target student to a single binary model file for the C runtime.

Layout:
  header (fixed, 4KB) : metadata + offsets to every float array and to the
                        int8 weight / scale sections
  float section       : all fp32 weights/biases (convnet, in_conv, depthwise,
                        LN, biases, proj, transformer norms, out_conv, label)
  scale section       : per-output-channel weight scales (fp32)
  int8 section        : packed gemm weights (W[input][output], 512B row stride)
"""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch, struct
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"stage3_anchor_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read

net, _ = load_model(False)
ck = torch.load(OUT/"checkpoint_step2000.pt", map_location="cpu", weights_only=True)
net.load_state_dict(ck["model"], strict=True); net.eval()
sd = net.state_dict()

# ---- collect float arrays (name -> np.float32) ----
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
# DCC per block
for i in range(8):
    p = f"mask_gen.encoder.dcc_layers.dcc_{i}.layers"
    add(f"dcc{i}.dw", sd[f"{p}.0.weight"].numpy())
    add(f"dcc{i}.db", sd[f"{p}.0.bias"].numpy())
    add(f"dcc{i}.ln1w", sd[f"{p}.1.weight"].numpy())
    add(f"dcc{i}.ln1b", sd[f"{p}.1.bias"].numpy())
    add(f"dcc{i}.pb", sd[f"{p}.3.bias"].numpy())   # pointwise bias
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

# label embedding constant (label=0 -> only biases then LN/ReLU/linear)
label = torch.zeros(1,1)
with torch.no_grad():
    lconst = net.label_embedding(label)[0].numpy()
add("label", lconst)

# ---- gemm matrices: quantize + pack ----
def quant_pack(weight):
    """weight torch [out, in]. Returns (packed bytes uint8 [in*512], scales [out])."""
    W = weight.detach()
    if W.dim() == 3:
        W = W.squeeze(-1)
    W = W.numpy().astype(np.float32)
    out_c, in_c = W.shape
    amax = np.max(np.abs(W), axis=1).clip(1e-8)
    sw = (amax/127.0)
    Wq = np.round(W/sw[:,None]).clip(-128,127).astype(np.int8)  # [out,in]
    packed = np.zeros((in_c,512), dtype=np.uint8)
    # packed[k,j] = Wq[j,k]
    packed[:, :out_c] = Wq.T.view(np.uint8)
    return packed.reshape(-1), sw.astype(np.float32)

# matrix descriptor list: (name, out_c, in_c, frames)
mats = []
for i in range(8):
    mats.append((f"enc{i}", 512, 512, 13))
for att in ["self","cross"]:
    mats.append((f"{att}_q", 256,256,13))
    mats.append((f"{att}_k", 256,256,26))
    mats.append((f"{att}_v", 256,256,26))
    mats.append((f"{att}_o", 256,256,13))
mats.append(("ffn1", 512,256,13))
mats.append(("ffn2", 256,512,13))
assert len(mats)==18

packed_list, scale_list, mat_desc = [], [], []
for name, oc, ic, fr in mats:
    if name.startswith("enc"):
        i = int(name[3:]); W = sd[f"mask_gen.encoder.dcc_layers.dcc_{i}.layers.3.weight"]
    elif name in ("self_q","self_k","self_v"):
        W = sd[f"{tl}.self_attn.in_proj_weight"][ {"q":0,"k":1,"v":2}[name[-1]]*256: ({"q":0,"k":1,"v":2}[name[-1]]+1)*256 ]
    elif name == "self_o":
        W = sd[f"{tl}.self_attn.out_proj.weight"]
    elif name in ("cross_q","cross_k","cross_v"):
        W = sd[f"{tl}.multihead_attn.in_proj_weight"][ {"q":0,"k":1,"v":2}[name[-1]]*256: ({"q":0,"k":1,"v":2}[name[-1]]+1)*256 ]
    elif name == "cross_o":
        W = sd[f"{tl}.multihead_attn.out_proj.weight"]
    elif name == "ffn1":
        W = sd[f"{tl}.linear1.weight"]
    elif name == "ffn2":
        W = sd[f"{tl}.linear2.weight"]
    pk, sc = quant_pack(W)
    mat_desc.append((name, oc, ic, fr, len(packed_list) if packed_list else 0, len(scale_list) if scale_list else 0))
    packed_list.append(pk); scale_list.append(sc)

# ---- assemble ----
HDR = 4096
float_blob = np.concatenate([a for _,a in floats]).astype(np.float32)
scale_blob = np.concatenate(scale_list).astype(np.float32)
packed_blob = np.concatenate(packed_list).astype(np.uint8)

# offsets
float_off = HDR
scale_off = float_off + float_blob.nbytes
packed_off = scale_off + scale_blob.nbytes
# per-float array offsets (fixed order/index)
float_arr_off = np.zeros(128, dtype=np.uint32)
acc = 0
for idx, (name, a) in enumerate(floats):
    float_arr_off[idx] = acc; acc += a.nbytes
assert len(floats) == 125, len(floats)
# per-matrix packed/scale offsets (fixed order)
mat_packed_off = np.zeros(18, dtype=np.uint32)
mat_scale_off = np.zeros(18, dtype=np.uint32)
accp, accs = 0, 0
for midx, ((name, oc, ic, fr, _, _), pk, sc) in enumerate(zip(mat_desc, packed_list, scale_list)):
    mat_packed_off[midx] = accp; mat_scale_off[midx] = accs
    accp += pk.nbytes; accs += sc.nbytes

# fixed binary header (little-endian), see model_header_t in llvc_runtime.h
header = struct.pack("<8I",
    0x4C4C5643, 1,        # magic 'CLVC', version
    16, 512, 256, 13, 13, 0)  # L, enc_dim, dec_dim, chunk, ctx_len, pad
header += struct.pack("<3I", float_off, scale_off, packed_off)
header += float_arr_off.astype("<u4").tobytes()
header += mat_packed_off.astype("<u4").tobytes()
header += mat_scale_off.astype("<u4").tobytes()
assert len(header) < HDR

model_path = BUD/"llvc_deploy_model.bin"
with open(model_path, "wb") as f:
    f.write(header)
    f.write(b"\x00" * (HDR - len(header)))
    f.write(float_blob.tobytes())
    f.write(scale_blob.tobytes())
    f.write(packed_blob.tobytes())
print("WROTE", model_path, "size", model_path.stat().st_size)
print("float bytes", float_blob.nbytes, "scale bytes", scale_blob.nbytes, "packed bytes", packed_blob.nbytes)
