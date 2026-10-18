"""Deterministic candidate generation for automatic multi-speaker screening.
Three model checkpoints and retrieval rates; same text input remains unchanged.
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

BASE=Path(__file__).resolve().parent
ROOT=BASE/'RVC'
OUT=Path('D:/总进度/目标人物分析/自动评估与改进/候选输出')
SAME_TEXT=Path('D:/总进度/目标人物分析/素材同文本普通声转换对比')

def main():
    pilot.settings()
    sys.path.insert(0,str(ROOT))
    os.chdir(ROOT)
    from infer.cli import create_config
    from infer.vc.modules import VC
    import pitch_conditioning_experiment as conditioning
    conditioning.verify_mapping()
    OUT.mkdir(parents=True,exist_ok=True)
    # Baseline has a separate copy and is never overwritten by continued training.
    models=[('e60',ROOT/'assets/weights/target_person_corrected.pth')]
    weights=ROOT/'assets/weights'
    for epoch in [90,120]:
        found=sorted(weights.glob(f'target_person_moretraining_e{epoch}_s*.pth'))
        if not found: raise FileNotFoundError('Checkpoint e'+str(epoch))
        models.append(('e'+str(epoch),found[-1]))
    previous=json.loads(Path('D:/总进度/目标人物分析/现有素材修正训练_中文真人对比/对比记录.json').read_text(encoding='utf-8-sig'))
    tests=[dict(name='same_text',source=str(SAME_TEXT/'普通合成声_原始.wav'),
                expected_text=(SAME_TEXT/'素材前15秒_识别文本.txt').read_text(encoding='utf-8').strip(),
                text_origin='ASR-derived target text',same_text_target=str(SAME_TEXT/'目标人物原声_试听.wav'))]
    for sample in ['BAC009S0002W0122','BAC009S0003W0121']:
        prior=next(x for x in previous['files'] if x['sample']==sample)
        tests.append(dict(name=sample,source=str(BASE/'public_chinese_test'/(sample+'.wav')),
                          expected_text=prior['text'],text_origin='AISHELL supplied transcript'))
    index=next((ROOT/'logs/target_person_corrected').glob('added_IVF*_Flat_nprobe_1_*.index'))
    config=create_config()
    baseline=json.loads((OUT.parent/'baseline_评估记录.json').read_text(encoding='utf-8'))
    reference_pitch=baseline['target_reference_pitch']
    target_center=float(np.median([np.log(x['median_hz']) for x in reference_pitch]))
    target_width=float(np.median([np.log(x['p90_hz']/x['p10_hz']) for x in reference_pitch]))
    records=[]
    for label,model in models:
        vc=VC(config)
        vc.get_vc(model.name)
        digest=hashlib.sha256(model.read_bytes()).hexdigest()
        original_get_f0=vc.pipeline.get_f0
        configurations=[(rate,'original') for rate in [0.,.35,.75]]
        if label in ['e60','e120']:
            configurations += [(rate,policy) for rate in [.35,.75] for policy in ['target_range','target_range_uv']]
        for rate,policy in configurations:
            vc.pipeline.get_f0=original_get_f0
            conditioning.install(vc,policy,target_center,target_width)
            for test in tests:
                random.seed(20261003)
                np.random.seed(20261003)
                torch.manual_seed(20261003)
                torch.cuda.manual_seed_all(20261003)
                status,result=vc.vc_single(0,test['source'],0,'rmvpe',str(index),rate,0,1.,.33)
                if not result or result[0] is None or result[1] is None: raise RuntimeError(status)
                sr,audio=result
                if np.issubdtype(audio.dtype,np.integer): audio=audio.astype(np.float64)/(np.iinfo(audio.dtype).max+1)
                rms=float(np.sqrt(np.mean(audio*audio)))
                peak=float(np.max(np.abs(audio)))
                if not np.isfinite(audio).all() or rms<=0: raise RuntimeError('Invalid audio')
                output=OUT/f'{label}_index{rate:.2f}_{policy}_{test["name"]}.wav'
                sf.write(output,audio*min(.04/rms,.95/peak),sr,subtype='PCM_16')
                original=sf.info(test['source'])
                if abs(len(audio)/sr-original.duration)>.1: raise RuntimeError('Duration mismatch')
                record=dict(label=f'{label}_index{rate:.2f}_{policy}_{test["name"]}',group=f'{label}_index{rate:.2f}_{policy}',
                    epoch=int(label[1:]),index_rate=rate,path=str(output),model=str(model),model_sha256=digest,
                    expected_text=test['expected_text'],text_origin=test['text_origin'],test_name=test['name'],
                    pitch_policy=policy,causal_streaming=False,source_speaker_enrollment=False)
                if policy!='original': record['conditioning_metadata']=vc.pitch_experiment_metadata
                if test.get('same_text_target'): record['same_text_target']=test['same_text_target']
                records.append(record)
                print('Generated '+record['label'],flush=True)
        del vc
        torch.cuda.empty_cache()
    (OUT.parent/'candidate_items.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Generated '+str(len(records))+' candidate clips',flush=True)

if __name__=='__main__': main()
