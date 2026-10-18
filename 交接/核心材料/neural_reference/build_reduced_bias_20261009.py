"""Load LLVC with a zero-initialized additive timbre branch."""
from pathlib import Path
import ast,zipfile,json,math
import torch,torch.nn as nn

BASE=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR=BASE/"neural_reference"

def build_net_bias(config_path):
    wheel=NR/"dependency_source_audit/speechbrain-0.5.16-py3-none-any.whl"
    with zipfile.ZipFile(wheel) as z:
        text=z.read("speechbrain/lobes/models/transformer/Transformer.py").decode()
    cls=next(n for n in ast.parse(text).body if isinstance(n,ast.ClassDef) and n.name=="PositionalEncoding")
    ns=dict(torch=torch,nn=nn,math=math,__name__="r")
    exec(compile(ast.Module(body=[cls],type_ignores=[]),"w","exec"),ns)
    path=NR/"LLVC/model_additive_bias_20261009.py"
    tree=ast.parse(path.read_text(encoding="utf-8"))
    tree.body=[n for n in tree.body if not (isinstance(n,ast.ImportFrom) and n.module=="speechbrain.lobes.models.transformer.Transformer")]
    namespace=dict(PositionalEncoding=ns["PositionalEncoding"],__name__="llvc_bias")
    exec(compile(tree,str(path),"exec"),namespace)
    cfg=json.loads(Path(config_path).read_text())
    return namespace["Net"](**cfg["model_params"]).eval()
