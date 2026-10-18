"""Matched-model conversions of new generic same-text Mandarin controls."""
from pathlib import Path
from types import SimpleNamespace
import argparse,hashlib,json,sys,time,os,random
import numpy as np
import soundfile as sf
import torch
import personalize_seed_teacher as personal
BASE=personal.BASE;OUT=Path('D:/总进度/目标人物分析/音色与自然度复查')
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def seed():
    assets,paths,get=personal.pinned_loaders()
    import inference
    loader=inference.load_models
    config='D:/总进度/目标人物分析/SeedVC人物微调/personal_strong_config.yml'
    selected=next(r for r in read(personal.OUT/'training_run.json')['checkpoints'] if r['step']==300)
    assert sha(selected['path'])==selected['sha256']
    candidates=[('seed_generic_reference',paths[('Plachta/Seed-VC','DiT_seed_v2_uvit_whisper_small_wavenet_bigvgan_pruned.pth')],.7),
        ('seed_personal300_cfg03',selected['path'],.3)]
    target=Path('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav')
    records=[]
    for group,checkpoint,cfg in candidates:
        kwargs=dict(diffusion_steps=30,length_adjust=1.0,inference_cfg_rate=cfg,f0_condition=False,
            auto_f0_adjust=False,semi_tone_shift=0,checkpoint=checkpoint,config=config,fp16=True)
        loaded=loader(SimpleNamespace(**kwargs));inference.load_models=lambda _:loaded
        folder=OUT/group;folder.mkdir(exist_ok=True)
        for row in read(OUT/'neural_control_manifest.json')['files']:
            x,sr=sf.read(row['path'],dtype='float32');x*=.04/max(float(np.sqrt(np.mean(x*x))),1e-8)
            inputs=OUT/'inputs';inputs.mkdir(exist_ok=True);source=inputs/(row['voice']+'.wav');sf.write(source,x,sr,subtype='PCM_24')
            torch.manual_seed(20261003);torch.cuda.synchronize();started=time.perf_counter()
            inference.main(SimpleNamespace(**kwargs,source=str(source),target=str(target),output=str(folder)))
            torch.cuda.synchronize();elapsed=time.perf_counter()-started
            output=folder/f'vc_{source.stem}_{target.stem}_1.0_30_{cfg}.wav'
            records.append(dict(label=group+'_'+row['voice'],group=group,test_name=row['voice'],path=str(output),sha256=sha(output),
                source_path=row['path'],source_sha256=sha(row['path']),expected_text=row['expected_text'],text_origin=row['text_origin'],
                checkpoint=str(checkpoint),checkpoint_sha256=sha(checkpoint),reference=str(target),reference_sha256=sha(target),
                cfg=cfg,steps=30,offline_file_seconds=elapsed,source_speaker_enrollment=False,board_deployed=False,
                same_text_target='D:/总进度/目标人物分析/素材同文本普通声转换对比/目标人物原声_试听.wav'))
            save(OUT/'seed_neural_items.json',records)
        inference.load_models=loader;del loaded;torch.cuda.empty_cache()
    print('Seed new-source controls completed',flush=True)

def rvc():
    root=BASE/'RVC';os.chdir(root);sys.path.insert(0,str(root))
    from infer.cli import create_config
    from infer.vc.modules import VC
    import pitch_conditioning_experiment as conditioning
    baseline=read(Path('D:/总进度/目标人物分析/自动评估与改进/baseline_评估记录.json'))
    reference=baseline['target_reference_pitch']
    center=float(np.median([np.log(r['median_hz']) for r in reference]));width=float(np.median([np.log(r['p90_hz']/r['p10_hz']) for r in reference]))
    selected=read(Path('D:/总进度/目标人物分析/自动评估与改进/当前自动候选.json'))['selected']
    checkpoint=Path(selected['model']);assert sha(checkpoint)==selected['model_sha256']
    vc=VC(create_config());vc.get_vc(checkpoint.name);conditioning.install(vc,'target_range',center,width)
    index=next((root/'logs/target_person_corrected').glob('added_IVF*_Flat_nprobe_1_*.index'))
    inputs=OUT/'inputs';inputs.mkdir(exist_ok=True);folder=OUT/'rvc_neural_controls';folder.mkdir(exist_ok=True)
    records=[]
    for row in read(OUT/'neural_control_manifest.json')['files']:
        x,sr=sf.read(row['path'],dtype='float32');x*=.04/max(float(np.sqrt(np.mean(x*x))),1e-8)
        path=inputs/(row['voice']+'_rvc.wav');sf.write(path,x,sr,subtype='FLOAT')
        random.seed(20261003);np.random.seed(20261003);torch.manual_seed(20261003)
        status,result=vc.vc_single(0,str(path),0,'rmvpe',str(index),.75,0,1.,.33)
        if not result or result[0] is None or result[1] is None:raise RuntimeError(status)
        rate,x=result
        if np.issubdtype(x.dtype,np.integer):x=x.astype('float64')/(np.iinfo(x.dtype).max+1)
        assert np.isfinite(x).all() and np.sqrt(np.mean(x*x))>1e-6
        x=x*min(.04/float(np.sqrt(np.mean(x*x))),.95/float(np.max(np.abs(x))))
        dest=folder/(row['voice']+'.wav');sf.write(dest,x,rate,subtype='PCM_16')
        records.append(dict(label='rvc_e120_neural_'+row['voice'],group='rvc_e120_neural',test_name=row['voice'],
            path=str(dest),sha256=sha(dest),source_path=row['path'],source_sha256=sha(row['path']),
            expected_text=row['expected_text'],text_origin=row['text_origin'],checkpoint=str(checkpoint),checkpoint_sha256=sha(checkpoint),
            source_speaker_enrollment=False,board_deployed=False,causal_streaming=False,pitch_policy='whole_utterance_target_range',
            same_text_target='D:/总进度/目标人物分析/素材同文本普通声转换对比/目标人物原声_试听.wav'))
    save(OUT/'rvc_neural_items.json',records);print('RVC new-source controls completed',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['seed','rvc'],default='seed');args=parser.parse_args()
    if args.stage=='seed':seed()
    else:rvc()
