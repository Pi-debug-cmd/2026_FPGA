"""Same real Mandarin samples, original e20 / corrected e20 / corrected e60.
No input speaker enrollment; source WAVs are never used for target training.
All variants are offline teacher tests, not board inference.
"""
from pathlib import Path
import hashlib,json,urllib.request
import numpy as np
import soundfile as sf
import torch
import run_rvc_pilot as pilot

BASE=Path(__file__).resolve().parent
ROOT=BASE/'RVC'
SOURCES=BASE/'public_chinese_test'
OUT=Path('D:/总进度/目标人物分析/现有素材修正训练_中文真人对比')
EXP=ROOT/'logs'/'target_person_corrected'

def normalize(path,destination):
    x,sr=sf.read(path,dtype='float64',always_2d=True)
    peak=float(np.max(np.abs(x)))
    rms=float(np.sqrt(np.mean(x*x)))
    if not np.isfinite(x).all() or peak==0 or rms==0:
        raise RuntimeError('Nonfinite or silent signal: '+str(path))
    gain=min(.04/rms,.95/peak)
    sf.write(destination,x*gain,sr,subtype='PCM_16')
    y,_=sf.read(destination)
    return dict(path=str(destination),seconds=len(x)/sr,sr=sr,
                rms=float(np.sqrt(np.mean(y*y))),peak=float(np.max(np.abs(y))),
                sha256=hashlib.sha256(destination.read_bytes()).hexdigest())

def main():
    pilot.EXP=EXP
    pilot.settings()
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((SOURCES/'source_manifest.json').read_text(encoding='utf-8'))
    revision=manifest['revision']
    ids={Path(f['path']).stem for f in manifest['files']}
    transcript={}
    url='https://huggingface.co/datasets/AISHELL/AISHELL-1/resolve/'+revision+'/data_aishell/transcript/aishell_transcript_v0.8.txt'
    with urllib.request.urlopen(url,timeout=60) as response:
        for raw in response:
            line=raw.decode('utf-8').strip()
            if not line: continue
            key,*words=line.split()
            if key in ids:
                transcript[key]=''.join(words)
                if len(transcript)==len(ids): break
    variants=[
        ('原始20轮',ROOT/'assets'/'weights'/'target_person_pilot.pth',
         ROOT/'logs'/'target_person_pilot'),
        ('修正20轮',ROOT/'assets'/'weights'/'target_person_corrected_e20_s300.pth',EXP),
        ('修正60轮',ROOT/'assets'/'weights'/'target_person_corrected.pth',EXP),
    ]
    records=[];models=[]
    for label,model,experiment in variants:
        if not model.is_file(): raise FileNotFoundError(model)
        index=next((experiment).glob('added_IVF*_Flat_nprobe_1_*.index'))
        ckpt=torch.load(model,map_location='cpu',weights_only=True)
        if not all(bool(torch.isfinite(t).all()) for t in ckpt['weight'].values()):
            raise RuntimeError('Nonfinite weights: '+str(model))
        models.append(dict(label=label,path=str(model),info=ckpt.get('info'),
                           bytes=model.stat().st_size,sha256=hashlib.sha256(model.read_bytes()).hexdigest(),
                           finite_weights=True,index=str(index)))
        del ckpt
        raw_out=OUT/(label+'_原始输出')
        raw_out.mkdir(exist_ok=True)
        pilot.command('compare_'+label,'-m','infer.cli','--model',model,
                      '--input',SOURCES,'--output',raw_out,'--pitch',0,
                      '--speaker-id',0,'--index',index,'--index-rate',.75,'--overwrite')
        for sample in manifest['files']:
            source=Path(sample['path'])
            produced=raw_out/source.name
            if not produced.is_file(): raise FileNotFoundError(produced)
            output=OUT/(source.stem+'_'+label+'.wav')
            checked=normalize(produced,output)
            source_info=sf.info(source)
            if abs(checked['seconds']-source_info.duration)>.1:
                raise RuntimeError('Audio duration mismatch')
            records.append(dict(speaker=sample['speaker'],gender_metadata=sample['gender_metadata'],
                                sample=source.stem,text=transcript.get(source.stem,''),
                                model_label=label,**checked))
    for sample in manifest['files']:
        source=Path(sample['path'])
        checked=normalize(source,OUT/(source.stem+'_转换前.wav'))
        records.append(dict(speaker=sample['speaker'],gender_metadata=sample['gender_metadata'],
                            sample=source.stem,text=transcript.get(source.stem,''),model_label='source',**checked))
    report=dict(target_training_original_seconds=99.13997916666668,
                heldout_target_seconds=22.84,pitch_semitones=0,index_rate=.75,
                source_enrollment=False,sources_not_used_for_target_training=True,
                corpus=manifest['dataset'],corpus_revision=revision,
                source_metadata_limit='Two distinct speakers, both labeled M by corpus; not evidence of all speakers or all conditions.',
                board_deployed=False,subjective_acceptance='pending',models=models,files=records)
    (OUT/'对比记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(models=models,checked_audio_files=len(records),
                         output=str(OUT),subjective_acceptance='pending'),ensure_ascii=False))

if __name__=='__main__': main()
