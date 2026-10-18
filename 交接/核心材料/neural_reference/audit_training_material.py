"""Quantify usable prepared speech; compare original and prepared input levels.
Reports signal estimates, not a perceptual or speaker-identity assessment.
"""
from pathlib import Path
import json
import numpy as np
import soundfile as sf
from run_rvc_pilot import BASE,ROOT,EXP,DATA,settings

def stats(path):
    x,sr=sf.read(path,always_2d=True)
    x=x.mean(axis=1)
    n=sr//50
    framed=x[:len(x)//n*n].reshape(-1,n)
    rms=np.sqrt(np.mean(framed*framed,axis=1))
    voiced=20*len(rms[rms>10**(-40/20)])/1000
    return dict(file=str(path),sample_rate=sr,seconds=len(x)/sr,
                peak=float(np.max(np.abs(x))),rms=float(np.sqrt(np.mean(x*x))),
                active_seconds_above_minus40db=voiced,finite=bool(np.isfinite(x).all()))

def main():
    settings()
    original=[stats(p) for p in sorted((DATA/'train').glob('*.wav'))]
    prepared=[stats(p) for p in sorted((EXP/'0_gt_wavs').glob('*.wav')) if p.stem!='pilot_mute']
    rows=[]
    for p in sorted((EXP/'3_feature768').glob('*.npy')):
        if p.stem=='pilot_mute': continue
        feature=np.load(p)
        f0=np.load(EXP/'2b-f0nsf'/(p.stem+'.wav.npy'))
        positive=f0[f0>0]
        rows.append(dict(name=p.stem,feature_shape=list(feature.shape),
                         feature_finite=bool(np.isfinite(feature).all()),
                         f0_finite=bool(np.isfinite(f0).all()),
                         f0_frames=len(f0),positive_f0_frames_after_interpolation=len(positive),
                         positive_f0_seconds_after_interpolation=len(positive)*.01,
                         f0_median=float(np.median(positive)) if len(positive) else None))
    # Compare each source duration with the surviving prepared pieces.
    per_source=[]
    for i,source in enumerate(original):
        matching=[r for r in prepared if Path(r['file']).stem.startswith(str(i)+'_')]
        per_source.append(dict(original=Path(source['file']).name,
                               original_seconds=source['seconds'],
                               prepared_seconds=sum(r['seconds'] for r in matching),
                               segments=len(matching)))
    result=dict(original_seconds=sum(r['seconds'] for r in original),
                prepared_seconds=sum(r['seconds'] for r in prepared),
                prepared_active_seconds=sum(r['active_seconds_above_minus40db'] for r in prepared),
                positive_f0_seconds_after_interpolation=sum(r['positive_f0_seconds_after_interpolation'] for r in rows),
                prepared_files=len(prepared),per_source=per_source,features=rows,
                all_prepared_audio_finite=all(r['finite'] for r in prepared),
                all_features_and_f0_finite=all(r['feature_finite'] and r['f0_finite'] for r in rows),
                limitations='Overlapping chunks double-count some time. The upstream F0 extractor interpolates unvoiced frames, so positive F0 duration is NOT voiced duration. Energy estimates do not measure clean intelligible speech or speaker similarity.')
    out=Path('D:/总进度/目标人物分析/训练材料复查_2026-10-03.json')
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='features'},ensure_ascii=False))

if __name__=='__main__': main()
