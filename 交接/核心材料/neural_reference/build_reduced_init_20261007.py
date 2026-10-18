"""Initialize reduced model (enc384/6 blocks, dec192/6 heads) by slicing stage3."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, ast, json, zipfile
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
import torch, torch.nn as nn, math

def build_net(config_path):
    wheel=NR/'dependency_source_audit/speechbrain-0.5.16-py3-none-any.whl'
    with zipfile.ZipFile(wheel) as z:
        text=z.read('speechbrain/lobes/models/transformer/Transformer.py').decode()
    cls=next(n for n in ast.parse(text).body if isinstance(n,ast.ClassDef) and n.name=='PositionalEncoding')
    ns=dict(torch=torch,nn=nn,math=math,__name__='r')
    exec(compile(ast.Module(body=[cls],type_ignores=[]),'w','exec'),ns)
    t=ast.parse((NR/'LLVC/model.py').read_text())
    t.body=[n for n in t.body if not (isinstance(n,ast.ImportFrom) and n.module=='speechbrain.lobes.models.transformer.Transformer')]
    nspace=dict(PositionalEncoding=ns['PositionalEncoding'],__name__='llvc_n')
    exec(compile(t,str(NR/'LLVC/model.py'),'exec'),nspace)
    cfg=json.loads(Path(config_path).read_text())
    return nspace['Net'](**cfg['model_params']).eval()

red=build_net(NR/'LLVC/experiments/llvc/config_reduced.json')
full_sd=torch.load(BUD/"stage3_anchor_student/checkpoint_step2000.pt",
                   map_location='cpu',weights_only=True)['model']
red_sd=red.state_dict()
out={}

def head_slice(w, nheads_old, nheads_new, dim=0):
    """slice first nheads_new heads (each head contiguous block of 32)."""
    hd=32
    if dim==0:
        return w[:nheads_new*hd]
    return w[:,:nheads_new*hd]

for k in red_sd:
    rs=red_sd[k].shape
    if k in full_sd and full_sd[k].shape==rs:
        out[k]=full_sd[k].clone(); continue
    # ---- structured slicing ----
    if k=="in_conv.0.weight":
        out[k]=full_sd[k][:384].clone()
    elif k.startswith("label_embedding.3"):
        out[k]=full_sd[k][:384].clone()
    elif k.startswith("label_embedding.4"):
        out[k]=full_sd[k][:384].clone()
    elif ".dcc_layers.dcc_" in k:
        layer=int(k.split(".layers.")[1].split(".")[0])
        if layer in (0,1,3,4):
            w=full_sd[k]
            if w.dim()==3:  # pointwise layer 3: slice rows+cols
                out[k]=w[:384,:384].clone()
            else:  # depthwise weight, LN, bias
                out[k]=w[:384].clone()
    elif k.startswith("mask_gen.proj_e2d"):
        # 256 -> 192
        out[k]=full_sd[k][:192].clone()
    elif k.startswith("mask_gen.proj_d2e"):
        # 512 -> 384
        out[k]=full_sd[k][:384].clone()
    elif k=="mask_gen.decoder.pos_enc.pe":
        out[k]=full_sd[k][:,:,:192].clone()
    elif k.endswith("self_attn.in_proj_weight") or k.endswith("multihead_attn.in_proj_weight"):
        w=full_sd[k]
        Q=w[0:256,:192][:192]; K=w[256:512,:192][:192]; V=w[512:768,:192][:192]
        out[k]=torch.cat([Q,K,V],0).clone()
    elif k.endswith("self_attn.in_proj_bias") or k.endswith("multihead_attn.in_proj_bias"):
        b=full_sd[k]
        out[k]=torch.cat([b[0:256][:192],b[256:512][:192],b[512:768][:192]],0).clone()
    elif k.endswith("out_proj.weight"):
        out[k]=full_sd[k][:192,:192].clone()
    elif k.endswith("out_proj.bias"):
        out[k]=full_sd[k][:192].clone()
    elif k.endswith("linear1.weight"):
        out[k]=full_sd[k][:384,:192].clone()
    elif k.endswith("linear1.bias"):
        out[k]=full_sd[k][:384].clone()
    elif k.endswith("linear2.weight"):
        out[k]=full_sd[k][:192,:384].clone()
    elif k.endswith("linear2.bias"):
        out[k]=full_sd[k][:192].clone()
    elif k.endswith(("norm1.weight","norm1.bias","norm2.weight","norm2.bias","norm3.weight","norm3.bias")):
        out[k]=full_sd[k][:192].clone()
    elif k=="out_conv.0.weight":
        out[k]=full_sd[k][:384].clone()
    else:
        raise SystemExit("UNHANDLED KEY "+k)

missing=[k for k in red_sd if k not in out]
assert not missing, missing
red.load_state_dict(out, strict=True)
OUT=BUD/"reduced_init"; OUT.mkdir(parents=True,exist_ok=True)
torch.save(dict(model=out),OUT/"reduced_init.pt")
print("REDUCED_INIT_OK params",sum(p.numel() for p in red.parameters()))
