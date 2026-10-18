"""Dump full and reduced model state dict keys/shapes for weight slicing."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, json
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
import torch
from load_llvc_audit_model import load_model

# reduced model built by the same loader machinery but with reduced config
import ast, zipfile
def load_reduced():
    wheel = NR/'dependency_source_audit/speechbrain-0.5.16-py3-none-any.whl'
    with zipfile.ZipFile(wheel) as z:
        text = z.read('speechbrain/lobes/models/transformer/Transformer.py').decode()
    tree0 = ast.parse(text)
    cls = next(n for n in tree0.body if isinstance(n, ast.ClassDef) and n.name=='PositionalEncoding')
    import math
    ns=dict(torch=torch, __name__='r')
    import torch.nn as nn
    exec(compile(ast.Module(body=[cls], type_ignores=[]), 'w', 'exec'),
         dict(torch=torch, nn=nn, math=math, __name__='r'), ns)
    src = (NR/'LLVC/model.py').read_text()
    t = ast.parse(src)
    t.body=[n for n in t.body if not (isinstance(n,ast.ImportFrom) and n.module=='speechbrain.lobes.models.transformer.Transformer')]
    nspace=dict(PositionalEncoding=ns['PositionalEncoding'], __name__='llvc_red')
    exec(compile(t, str(NR/'LLVC/model.py'), 'exec'), nspace)
    cfg=json.loads((NR/'LLVC/experiments/llvc/config_reduced.json').read_text())
    net=nspace['Net'](**cfg['model_params']).eval()
    return net

full,_=load_model(False)
red=load_reduced()
full_sd=torch.load(BASE/"board_budget_20261005/stage3_anchor_student/checkpoint_step2000.pt",
                  map_location='cpu', weights_only=True)['model']
print("=== keys only in reduced (need mapping) ===")
for k in red.state_dict():
    rs=red.state_dict()[k].shape
    if k in full_sd:
        fs=full_sd[k].shape
        flag='' if fs==rs else '  <-- SHAPE %s vs %s'%(fs,rs)
        print(k, tuple(rs), flag)
    else:
        print(k, tuple(rs), '  <-- MISSING IN FULL')
