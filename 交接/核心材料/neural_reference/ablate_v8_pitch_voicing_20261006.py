"""Three fixed causal feature ablations. Offline only; not a new accepted model."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import numpy as np, json, subprocess, soundfile as sf

base=Path(__file__).resolve().parent
budget=base.parent/'board_budget_20261005'
native=base.parent/'board_support/native_llvc_20261005'
original=json.loads((budget/'fargan_mapper_expanded_v8/decision.json').read_text(encoding='utf-8'))
variants=('fargan_v8_pitch_smooth','fargan_v8_source_voicing','fargan_v8_pitch_smooth_source_voicing')

def smooth(features):
    result=features.copy();prev=None
    for i,row in enumerate(features):
        if row[0]>-7 and row[19]>.1:
            value=float(row[18])
            if prev is not None: value=prev+.45*(value-prev)
            prev=value;result[i,18]=value
        else: prev=None
    return result

for variant in variants:
    out=budget/variant;out.mkdir(exist_ok=True);outputs=[]
    for row in original['heldout_outputs']:
        assert row['split']=='validation'
        stem=Path(row['filename']).stem
        converted=np.fromfile(budget/'fargan_mapper_expanded_v8'/(stem+'.converted.f32'),dtype='float32').reshape(-1,20)
        source=np.fromfile(row['source_features'],dtype='float32').reshape(-1,20)
        if 'pitch_smooth' in variant: converted=smooth(converted)
        else: converted=converted.copy()
        if 'source_voicing' in variant: converted[:,19]=source[:len(converted),19]
        features=out/(stem+'.converted.f32');pcm=out/(stem+'.pcm')
        converted.astype('float32').tofile(features)
        subprocess.run([str(native/'fargan_probe_host.exe'),'--synthesis',str(features),str(pcm),str(out/(stem+'.synthesis.json'))],check=True)
        wave=np.fromfile(pcm,dtype='<i2').astype('float32')/32768
        path=out/(stem+'_student.wav');sf.write(path,wave,16000,subtype='FLOAT')
        outputs.append(dict(row,student_path=str(path)))
    report=dict(complete=True,heldout_outputs=outputs,quality_accepted=False,board_live_deployed=False,
                source_enrollment=False,raw_waveform_mix=False,recognizer_used_as_loss=False,
                auxiliary_speaker_loss_used=False,test_audio_used=False,
                causal_pitch_ema_alpha=.45 if 'pitch_smooth' in variant else None,
                source_periodicity_preserved='source_voicing' in variant,
                diagnostic_ablation_only=True,origin='rejected V8 unchanged weights')
    (out/'decision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('ABLATION_READY',variant,flush=True)
