"""Audit fixed-male recordings1-3 against Round91 public prosody statistics.

Run after preparing and training Round91; never reads recordings4/5 or Track9.
"""
import argparse
import json
from pathlib import Path
import sys
import torch

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--asset-root', required=True, type=Path)
root = parser.parse_args().asset_root.resolve()
run = root / 'build/generated/hubert_world_round91_20261027'
torch.set_num_threads(1)
for dep in reversed(('llvc_cpu_deps', 'seed_audio_deps', 'seed_cpu_deps', 'world_deps')):
    sys.path.insert(0, str(root / 'build/generated' / dep))
schema = torch.library.Library('torchvision', 'DEF')
schema.define('nms(Tensor boxes, Tensor scores, float iou_threshold) -> Tensor')
sys.path.insert(0, str(run / 'runtime/build'))
import train_hubert_world_teacher_round20_20261025 as base
import audit_source_prosody_round32_20261025 as prosody
import numpy as np

cp = torch.load(run / 'paired_causal_gru.pt', map_location='cpu', weights_only=False)
rows = []
features = []
for number in (1, 2, 3):
    path = root / f'人物音频资料/男声/标准录音 {number}.wav'
    signal = base.read_16k(path)
    value = prosody.source_prosody(signal)
    z = (value - cp['prosody_mean']) / cp['prosody_std']
    features.append(value)
    rows.append({'recording': number, 'sha256': base.sha256(path),
                 'seconds': len(signal) / 16000, 'rms': float(np.sqrt(np.mean(signal ** 2))),
                 'prosody_mean': value.mean(axis=0).tolist(),
                 'prosody_std': value.std(axis=0).tolist(),
                 'z_mean': z.mean(axis=0).tolist(),
                 'z_abs_over3_fraction': (np.abs(z) > 3).mean(axis=0).tolist()})
pooled = np.concatenate(features)
audit = {'kind': 'fixed_male_prosody_distribution_audit', 'columns': ['log_f0', 'vuv', 'log_energy'],
         'checkpoint_sha256': base.sha256(run / 'paired_causal_gru.pt'),
         'public_training_prosody_mean': cp['prosody_mean'].tolist(),
         'public_training_prosody_std': cp['prosody_std'].tolist(),
         'fixed_male_pooled_mean': pooled.mean(axis=0).tolist(),
         'fixed_male_pooled_std': pooled.std(axis=0).tolist(), 'rows': rows,
         'recording4_used': False, 'recording5_used': False, 'target_track9_used': False,
         'modified_training_or_candidate': False, 'played': False, 'board_touched': False}
(run / 'fixed_male_prosody_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(audit, ensure_ascii=False), flush=True)
