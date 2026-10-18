"""Minimal isolated loader: original LLVC architecture, no training imports."""
import ast
import json
import math
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build/generated/llvc_cpu_deps'))
import torch
from torch import nn


def load_v2():
    original = ROOT / '交接/核心材料/neural_reference'
    snapshot = ROOT / 'build/generated/llvc_host_audit_20261015/python_snapshot'
    snapshot.mkdir(parents=True, exist_ok=True)
    for name in ['model.py', 'cached_convnet.py']:
        shutil.copyfile(original / 'LLVC' / name, snapshot / name)
    shutil.copyfile(original / 'llvc_online_stream.py', snapshot / 'llvc_online_stream.py')
    sys.path.insert(0, str(snapshot))
    wheel = original / 'dependency_source_audit/speechbrain-0.5.16-py3-none-any.whl'
    with zipfile.ZipFile(wheel) as package:
        tree = ast.parse(package.read('speechbrain/lobes/models/transformer/Transformer.py').decode())
    positional = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'PositionalEncoding')
    namespace = {'torch': torch, 'nn': nn, 'math': math, '__name__': 'llvc_positional_reference'}
    exec(compile(ast.Module(body=[positional], type_ignores=[]), str(wheel), 'exec'), namespace)
    tree = ast.parse((snapshot / 'model.py').read_text(encoding='utf-8'))
    tree.body = [node for node in tree.body if not (isinstance(node, ast.ImportFrom) and
                 node.module == 'speechbrain.lobes.models.transformer.Transformer')]
    namespace = {'PositionalEncoding': namespace['PositionalEncoding'], '__name__': 'llvc_model_reference'}
    exec(compile(tree, str(snapshot / 'model.py'), 'exec'), namespace)
    config_path = original / 'LLVC/experiments/llvc/config_reduced.json'
    config = json.loads(config_path.read_text(encoding='utf-8'))
    model = namespace['Net'](**config['model_params']).eval()
    checkpoint = ROOT / '交接/核心材料/board_budget_20261005/reduced_student_v2/final.pt'
    state = torch.load(checkpoint, map_location='cpu', weights_only=True)
    model.load_state_dict(state['model'], strict=True)
    return model, checkpoint, config_path, snapshot
