"""Isolated official Seed V1 personal fine-tuning and fixed-input evaluation.

No board writes, source enrollment, target-original modification or audio upload.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import random
import sys
import time
from types import SimpleNamespace
import numpy as np
import soundfile as sf
import torch
import yaml
from scipy.signal import resample_poly
from math import gcd
import run_rvc_pilot as pilot

pilot.settings()
BASE=Path(__file__).resolve().parent
ROOT=BASE/'Seed-VC'
PINNED=ROOT/'checkpoints/pinned'
OUT=Path('D:/总进度/目标人物分析/SeedVC人物微调')
OUT.mkdir(parents=True,exist_ok=True)
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
os.chdir(ROOT)
sys.path.insert(0,str(ROOT))
torch.set_num_threads(4)

def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value): Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def pinned_loaders():
    assets=[]
    for name in ['manifest.json','strong_manifest.json','training_manifest.json']:
        assets+=read(PINNED/name)
    paths={}
    for repo in assets:
        for row in repo['files']:
            if sha(row['path'])!=row['sha256']: raise RuntimeError('Asset hash mismatch')
            filename=row['url'].split('/resolve/'+repo['revision']+'/')[-1]
            paths[(repo['repository'],filename)]=row['path']
    def get(repo_id,model_filename='pytorch_model.bin',config_filename=None):
        if config_filename is None: return paths[(repo_id,model_filename)]
        return paths[(repo_id,model_filename)],paths[(repo_id,config_filename)]
    import hf_utils
    hf_utils.load_custom_model_from_hf=get
    import modules.commons as commons
    original=commons.load_checkpoint
    def checked(model,optimizer,path,*args,**kwargs):
        state=torch.load(path,map_location='cpu',weights_only=True)['net']
        for name,network in model.items():
            source={k.removeprefix('module.'):v for k,v in state[name].items()}
            for key,p in network.named_parameters():
                if key not in source or source[key].shape!=p.shape: raise RuntimeError('Missing/mismatched '+name+'/'+key)
        return original(model,optimizer,path,*args,**kwargs)
    commons.load_checkpoint=checked
    return assets,paths,get

def prepare():
    folder=OUT/'training_audio';folder.mkdir(exist_ok=True)
    records=[]; originals=[]
    for n in range(5,9):
        path=Path(f'D:/总进度/目标人物语音/Track {n}.wav')
        x,sr=sf.read(path,dtype='float32')
        if x.ndim==2:x=x.mean(axis=1)
        factor=gcd(sr,22050);x=resample_poly(x,22050//factor,sr//factor).astype(np.float32)
        x=x*.04/max(float(np.sqrt(np.mean(x*x))),1e-8)
        step=22050*4;start=0;index=0
        while start<len(x):
            end=min(start+step,len(x))
            if 0<len(x)-end<22050:end=len(x)
            clip=x[start:end]
            if len(clip)<22050:raise RuntimeError('Tail must not be silently dropped')
            dest=folder/f'track{n}_segment{index:02}.wav';sf.write(dest,clip,22050,subtype='PCM_24')
            records.append(dict(path=str(dest),sha256=sha(dest),original=str(path),original_sha256=sha(path),
                start_seconds=start/22050,seconds=len(clip)/22050))
            start=end;index+=1
        originals.append(dict(path=str(path),sha256=sha(path),seconds=len(x)/22050))
    held=Path('D:/总进度/目标人物语音/Track 9.wav')
    save(OUT/'training_split.json',dict(train_originals=originals,train_segments=records,
        total_seconds=sum(r['seconds'] for r in records),heldout=dict(path=str(held),sha256=sha(held),
        use='excluded from fine-tuning; previously repeatedly used as diagnostic, not pristine final holdout'),
        preprocessing='stereo average, polyphase22.05k, per-track RMS.04, contiguous4s splits with <1s tails merged; PCM24',
        source_validation_used_for_training=False,source_speaker_enrollment=False))
    cfg=yaml.safe_load(Path('D:/总进度/目标人物分析/SeedVC下一阶段/pinned_strong_config.yml').read_text(encoding='utf-8'))
    cfg['log_dir']=str(OUT/'runs');cfg['log_interval']=10;cfg['batch_size']=1
    config=OUT/'personal_strong_config.yml';config.write_text(yaml.safe_dump(cfg,allow_unicode=True),encoding='utf-8')
    return config,folder

def train_personal(steps):
    config,folder=prepare()
    assets,paths,get=pinned_loaders()
    import train
    train.load_custom_model_from_hf=get
    # Official loss never calls vocoder_fn. Skip that frozen unused network only.
    train.Trainer.build_vocoder=lambda self,device,config:setattr(self,'vocoder_fn',None)
    random.seed(20261003);np.random.seed(20261003);torch.manual_seed(20261003)
    started=time.perf_counter()
    trainer=train.Trainer(str(config),paths[('Plachta/Seed-VC','DiT_seed_v2_uvit_whisper_small_wavenet_bigvgan_pruned.pth')],
        str(folder),'target_person_300step',batch_size=1,num_workers=0,steps=steps,max_epochs=1000,device='cuda:0')
    trainer.whisper_model.eval().requires_grad_(False)
    trainer.campplus_model.eval().requires_grad_(False)
    trainer.tone_color_converter.model.eval().requires_grad_(False)
    # OpenVoice loader is permissive upstream; independently check every learned key.
    ov=torch.load(paths[('myshell-ai/OpenVoiceV2','converter/checkpoint.pth')],map_location='cpu',weights_only=True)['model']
    for name,p in trainer.tone_color_converter.model.named_parameters():
        if name not in ov or ov[name].shape!=p.shape:raise RuntimeError('OpenVoice learned parameter mismatch')
    del ov
    for network in trainer.model.values():network.train()
    initial={name:next(net.parameters()).detach().cpu().clone() for name,net in trainer.model.items()}
    rows=[];checkpoints=[];torch.cuda.reset_peak_memory_stats()
    try:
        while len(rows)<steps:
            for batch in trainer.train_dataloader:
                batch=[b.to(trainer.device) for b in batch]
                start=time.perf_counter();loss=trainer.train_one_step(batch);torch.cuda.synchronize()
                if not np.isfinite(loss):raise RuntimeError('Nonfinite loss')
                row=dict(step=len(rows)+1,loss=loss,wall_seconds=time.perf_counter()-start)
                rows.append(row)
                if row['step']%10==0:
                    print(f"STEP {row['step']}/{steps} loss={loss:.5f}",flush=True)
                    save(OUT/'training_progress.json',dict(status='running',completed_steps=len(rows),requested_steps=steps,last=row))
                if row['step'] in {100,steps}:
                    for net in trainer.model.values():
                        if any(not torch.isfinite(p).all() for p in net.parameters()):raise RuntimeError('Nonfinite trained weights')
                    dest=OUT/f'personal_step{row["step"]:03}.pth'
                    torch.save(dict(net={name:{k:v.detach().cpu() for k,v in net.state_dict().items()} for name,net in trainer.model.items()}),dest)
                    checkpoints.append(dict(step=row['step'],path=str(dest),sha256=sha(dest)))
                if len(rows)>=steps:break
        changed={name:not torch.equal(first,next(trainer.model[name].parameters()).detach().cpu()) for name,first in initial.items()}
        save(OUT/'training_run.json',dict(status='complete',steps=len(rows),seed=20261003,batch_size=1,
            precision='FP32 official loss/AdamW',learning_rate=1e-5,scheduler_gamma=.999996,
            config=str(config),config_sha256=sha(config),assets=assets,
            source_revision='51383efd921027683c89e5348211d93ff12ac2a8',
            official_loss_used=True,checkpoints=checkpoints,training_rows=rows,
            parameter_probe_changed=changed,wall_seconds=time.perf_counter()-started,
            peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),
            adaptations=['Skip frozen unused vocoder during training only','Freeze reference/semantic/augmentation networks in eval',
                'Batch1, zero data workers, deterministic4s slices with tails retained','Weights-only100/final checkpoints; no resumable optimizer export'],
            subjectively_accepted=False,board_deployed=False,audio_uploaded=False))
        save(OUT/'training_progress.json',dict(status='complete',completed_steps=len(rows),checkpoints=checkpoints))
        print('TRAIN COMPLETE',flush=True)
    except Exception as error:
        save(OUT/'training_progress.json',dict(status='failed',completed_steps=len(rows),error=repr(error),checkpoints=checkpoints))
        raise

def infer_personal(checkpoint_step=None,cfg=.7,diffusion_steps=30):
    assets,paths,get=pinned_loaders()
    import inference
    baseline=read(Path('D:/总进度/目标人物分析/自动评估与改进/baseline_评估记录.json'))
    sources=[r for r in baseline['files'] if r['label']=='ordinary_same_text' or r['label'].startswith('source_')]
    sources+=read(BASE/'public_chinese_validation/validation_manifest.json')['files']
    config=OUT/'personal_strong_config.yml';checkpoints=read(OUT/'training_run.json')['checkpoints']
    if checkpoint_step is not None:checkpoints=[r for r in checkpoints if r['step']==checkpoint_step]
    if not checkpoints:raise RuntimeError('Requested checkpoint absent')
    suffix=f'_cfg{cfg}_steps{diffusion_steps}' if cfg!=.7 or diffusion_steps!=30 else ''
    target=Path('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav')
    records=[];loader=inference.load_models
    for ckpt in checkpoints:
        if sha(ckpt['path'])!=ckpt['sha256']:raise RuntimeError('Checkpoint changed')
        kwargs=dict(diffusion_steps=diffusion_steps,length_adjust=1.0,inference_cfg_rate=cfg,f0_condition=False,
            auto_f0_adjust=False,semi_tone_shift=0,checkpoint=ckpt['path'],config=str(config),fp16=True)
        loaded=loader(SimpleNamespace(**kwargs));inference.load_models=lambda _:loaded
        folder=OUT/f'step{ckpt["step"]:03}{suffix}';folder.mkdir(exist_ok=True)
        input_folder=OUT/'test_inputs';input_folder.mkdir(exist_ok=True)
        for row in sources:
            x,sr=sf.read(row['path'],dtype='float32')
            if x.ndim==2:x=x.mean(axis=1)
            x=x*.04/max(float(np.sqrt(np.mean(x*x))),1e-8)
            name='same_text' if row['label']=='ordinary_same_text' else Path(row['path']).stem
            source=input_folder/(name+'.wav');sf.write(source,x,sr,subtype='PCM_24')
            torch.manual_seed(20261003);torch.cuda.synchronize();start=time.perf_counter()
            inference.main(SimpleNamespace(**kwargs,source=str(source),target=str(target),output=str(folder)))
            torch.cuda.synchronize();elapsed=time.perf_counter()-start
            output=folder/f'vc_{name}_{target.stem}_1.0_{diffusion_steps}_{cfg}.wav'
            audio,rate=sf.read(output)
            if not np.isfinite(audio).all() or np.sqrt(np.mean(audio*audio))<1e-6:raise RuntimeError('Invalid output')
            record=dict(label=f'seed_personal_{ckpt["step"]}{suffix}_{name}',group=f'seed_personal_{ckpt["step"]}{suffix}',
                test_name=name,path=str(output),sha256=sha(output),expected_text=row['expected_text'],text_origin=row['text_origin'],
                source_path=row['path'],source_sha256=sha(row['path']),checkpoint=ckpt,
                seconds=len(audio)/rate,offline_file_seconds=elapsed,source_speaker_enrollment=False,
                reference_path=str(target),reference_sha256=sha(target),board_deployed=False,subjective_acceptance=False,
                cfg=cfg,diffusion_steps=diffusion_steps,input_normalization='mono RMS.04, PCM24',seed=20261003)
            if name=='same_text':record['same_text_target']='D:/总进度/目标人物分析/素材同文本普通声转换对比/目标人物原声_试听.wav'
            records.append(record);save(OUT/f'personal{suffix}_items.json',records)
            print('OUTPUT '+record['label'],flush=True)
        inference.load_models=loader
        del loaded;torch.cuda.empty_cache()
    save(OUT/f'inference{suffix}_run.json',dict(status='complete',files=records,weights_finetuned=True,board_deployed=False,audio_uploaded=False))
    print('INFERENCE COMPLETE',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['train','infer'],required=True);p.add_argument('--steps',type=int,default=300)
    p.add_argument('--checkpoint-step',type=int);p.add_argument('--cfg',type=float,default=.7);p.add_argument('--diffusion-steps',type=int,default=30)
    args=p.parse_args()
    if args.stage=='train':train_personal(args.steps)
    else:infer_personal(args.checkpoint_step,args.cfg,args.diffusion_steps)
