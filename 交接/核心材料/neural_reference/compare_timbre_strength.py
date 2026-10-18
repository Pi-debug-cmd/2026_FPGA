"""Fixed e60 model, pitch and random seed; vary retrieval strength only.
Public source speech is evaluation-only. This is PC offline inference.
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
OUT = Path('D:/总进度/目标人物分析/音色参考强度对比_修正60轮')

def main():
    pilot.settings()
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    from infer.cli import create_config
    from infer.vc.modules import VC
    model = ROOT / 'assets/weights/target_person_corrected.pth'
    index = next((ROOT / 'logs/target_person_corrected').glob('added_IVF*_Flat_nprobe_1_*.index'))
    vc = VC(create_config())
    vc.get_vc(model.name)
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    for sample in ['BAC009S0002W0122', 'BAC009S0003W0121']:
        source = BASE / 'public_chinese_test' / (sample + '.wav')
        original, source_sr = sf.read(source)
        for label, rate in [('A_参考较弱', .35), ('B_当前参考', .75), ('C_参考较强', 1.0)]:
            random.seed(20261003)
            np.random.seed(20261003)
            torch.manual_seed(20261003)
            torch.cuda.manual_seed_all(20261003)
            status, result = vc.vc_single(0, str(source), 0, 'rmvpe', str(index), rate, 0, 1., .33)
            if not result or result[0] is None or result[1] is None:
                raise RuntimeError(status)
            sr, data = result
            if np.issubdtype(data.dtype, np.integer):
                data = data.astype(np.float64) / (np.iinfo(data.dtype).max + 1)
            else:
                data = data.astype(np.float64)
            peak = float(np.max(np.abs(data)))
            rms = float(np.sqrt(np.mean(data * data)))
            if not np.isfinite(data).all() or rms <= 0:
                raise RuntimeError('Nonfinite or silent: ' + label)
            if abs(len(data) / sr - len(original) / source_sr) > .1:
                raise RuntimeError('Duration mismatch')
            gain = min(.04 / rms, .95 / peak)
            output = OUT / (sample + '_' + label + '.wav')
            sf.write(output, data * gain, sr, subtype='PCM_16')
            check, _ = sf.read(output)
            if not np.isfinite(check).all() or np.max(np.abs(check)) >= 1:
                raise RuntimeError('Invalid saved audio')
            records.append(dict(sample=sample, label=label, index_rate=rate,
                                path=str(output), seconds=len(check)/sr,
                                rms=float(np.sqrt(np.mean(check * check))),
                                peak=float(np.max(np.abs(check))),
                                sha256=hashlib.sha256(output.read_bytes()).hexdigest()))
            print('Completed ' + sample + ' ' + label, flush=True)
    report = dict(model=str(model), model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),
                  index=str(index), pitch_semitones=0, protect=.33, seed=20261003,
                  changed_parameter='retrieval index_rate only', board_deployed=False,
                  source_enrollment=False, sources_used_in_training=False,
                  previous_user_feedback='Corrected e60 sounds closer than before; remaining gap is timbre thickness/nasality/breathiness.',
                  subjective_acceptance='pending', files=records)
    (OUT/'对比记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'试听说明.md').write_text(
        '# 音色参考强度对比\n\n'
        '同一修正60轮模型、同一输入语音、相同随机种子与音高设置，仅改变目标检索特征的混合比例。'
        'A=0.35，B=0.75，C=1.00；参考更强不保证更像或更自然。文件音量对齐。\n\n'
        '先比较同一句的A/B/C，选择更接近目标人物且吐字自然的一版；再用第二个不同说话人检查。'
        '两个公开输入说话人均未用于目标训练，也无需输入人物注册。\n\n'
        '这是电脑离线试听，未部署板卡；听感改进不能证明7020实时运行或任意说话人已经通过验收。\n',
        encoding='utf-8')
    print(json.dumps(dict(output=str(OUT), checked_files=len(records)),ensure_ascii=False),flush=True)

if __name__ == '__main__':
    main()
