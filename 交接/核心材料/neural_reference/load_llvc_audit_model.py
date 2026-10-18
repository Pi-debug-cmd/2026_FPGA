"""Load exact LLVC architecture and exact isolated positional-encoding source.

The official checkpoint used here is NOT the user's target voice. This loader
supports geometry, state, streaming and numeric audits, not identity acceptance.
"""
from pathlib import Path
import ast, math, sys, json, zipfile, hashlib
from run_rvc_pilot import settings
settings()
import torch
import torch.nn as nn

BASE = Path(__file__).resolve().parent
SOURCE = BASE / 'LLVC'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_model(checkpoint=True):
    wheel = BASE / 'dependency_source_audit/speechbrain-0.5.16-py3-none-any.whl'
    with zipfile.ZipFile(wheel) as z:
        text = z.read('speechbrain/lobes/models/transformer/Transformer.py').decode()
    cls = next(n for n in ast.parse(text).body
               if isinstance(n, ast.ClassDef) and n.name == 'PositionalEncoding')
    namespace = dict(torch=torch, nn=nn, math=math)
    exec(compile(ast.Module(body=[cls], type_ignores=[]),
                 str(wheel) + '::PositionalEncoding', 'exec'), namespace)
    tree = ast.parse((SOURCE / 'model.py').read_text())
    tree.body = [n for n in tree.body if not (
        isinstance(n, ast.ImportFrom) and
        n.module == 'speechbrain.lobes.models.transformer.Transformer')]
    sys.path.insert(0, str(SOURCE))
    namespace = dict(PositionalEncoding=namespace['PositionalEncoding'],
                     __name__='llvc_audit_architecture')
    exec(compile(tree, str(SOURCE / 'model.py'), 'exec'), namespace)
    config = json.loads((SOURCE / 'experiments/llvc/config.json').read_text())
    net = namespace['Net'](**config['model_params']).eval()
    if checkpoint:
        path = BASE / 'llvc_pretrained_audit/G_500000.pth'
        manifest = json.loads((path.parent / 'manifest.json').read_text())
        entry = next(r for r in manifest['files'] if r['remote_path'].endswith('.pth'))
        assert digest(path) == entry['sha256']
        state = torch.load(path, map_location='cpu', weights_only=True)
        net.load_state_dict(state['model'], strict=True)
    return net, config
