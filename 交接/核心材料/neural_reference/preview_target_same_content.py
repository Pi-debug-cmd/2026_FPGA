"""Held-out Track9 round trip, with original content and duration preserved.
This checks target reconstruction, not conversion of an unseen source speaker.
"""
from pathlib import Path
import hashlib
import json
import os
import random
import sys
import numpy as np
import soundfile as sf
import torch
import run_rvc_pilot as pilot

BASE = Path(__file__).resolve().parent
ROOT = BASE / 'RVC'
OUT = Path('D:/总进度/目标人物分析/Track9同内容原声与模型对比')
SOURCE = Path('D:/总进度/目标人物语音/Track 9.wav')

def crop_existing():
    records = []
    for source_name, destination_name in [
        ('Track9_原声.wav', 'Track9_前15秒_原声.wav'),
        ('Track9_模型处理后.wav', 'Track9_前15秒_模型处理后.wav')]:
        audio, sr = sf.read(OUT / source_name)
        audio = audio[:15 * sr]
        if len(audio) != 15 * sr:
            raise RuntimeError('Short source')
        records.append(save_aligned(audio, sr, destination_name))
    record = json.loads((OUT/'对比记录.json').read_text(encoding='utf-8'))
    record['audition_excerpt'] = dict(start_seconds=0, end_seconds=15,
        prepared_from_full_roundtrip=True, content_replaced=False, files=records)
    (OUT/'对比记录.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(excerpt_seconds=15,files=records),ensure_ascii=False),flush=True)

def save_aligned(data, sr, name):
    data = np.asarray(data, dtype=np.float64)
    if data.ndim == 2:
        data = data.mean(axis=1)
    rms = float(np.sqrt(np.mean(data * data)))
    peak = float(np.max(np.abs(data)))
    if not np.isfinite(data).all() or rms == 0:
        raise RuntimeError('Invalid audio')
    destination = OUT / name
    sf.write(destination, data * min(.04/rms, .95/peak), sr, subtype='PCM_16')
    saved, _ = sf.read(destination)
    if not np.isfinite(saved).all() or np.max(np.abs(saved)) >= 1:
        raise RuntimeError('Saved audio validation failed')
    return dict(path=str(destination), sr=sr, seconds=len(saved)/sr,
                peak=float(np.max(np.abs(saved))), rms=float(np.sqrt(np.mean(saved*saved))),
                sha256=hashlib.sha256(destination.read_bytes()).hexdigest())

def main():
    pilot.settings()
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    from infer.cli import create_config
    from infer.vc.modules import VC
    before_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    model = ROOT / 'assets/weights/target_person_corrected.pth'
    index = next((ROOT/'logs/target_person_corrected').glob('added_IVF*_Flat_nprobe_1_*.index'))
    OUT.mkdir(parents=True, exist_ok=True)
    original, sr = sf.read(SOURCE)
    original_record = save_aligned(original, sr, 'Track9_原声.wav')
    vc = VC(create_config())
    vc.get_vc(model.name)
    random.seed(20261003)
    np.random.seed(20261003)
    torch.manual_seed(20261003)
    torch.cuda.manual_seed_all(20261003)
    status, result = vc.vc_single(0, str(SOURCE), 0, 'rmvpe', str(index), .75, 0, 1., .33)
    if not result or result[0] is None or result[1] is None:
        raise RuntimeError(status)
    converted_sr, audio = result
    if np.issubdtype(audio.dtype, np.integer):
        audio = audio.astype(np.float64)/(np.iinfo(audio.dtype).max+1)
    converted_record = save_aligned(audio, converted_sr, 'Track9_模型处理后.wav')
    if abs(converted_record['seconds']-original_record['seconds']) > .1:
        raise RuntimeError('Duration mismatch')
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != before_hash:
        raise RuntimeError('Original changed')
    report = dict(source=str(SOURCE),source_sha256=before_hash,
                  source_is_target_person=True,source_held_out_from_training_and_index=True,
                  purpose='Held-out target reconstruction, not unseen-speaker conversion acceptance',
                  input_text_replaced=False,tts_used=False,cropped=False,
                  model=str(model),model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),
                  index_rate=.75,pitch_semitones=0,protect=.33,
                  board_deployed=False,subjective_acceptance='pending',
                  files=[original_record,converted_record])
    (OUT/'对比记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__ == '__main__':
    if '--crop-existing' in sys.argv:
        crop_existing()
    else:
        main()
        crop_existing()
