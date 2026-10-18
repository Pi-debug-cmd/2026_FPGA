"""Pinned XLSR-tiny zero-shot quality reference. PC only, no enrollment."""
from pathlib import Path
from types import SimpleNamespace
import hashlib,json,os,sys,time
import numpy as np
import soundfile as sf
import torch
import yaml
import run_rvc_pilot as pilot
pilot.settings()
BASE=Path(__file__).resolve().parent
ROOT=BASE/'Seed-VC'
PINNED=ROOT/'checkpoints'/'pinned'
OUT=Path('D:/总进度/目标人物分析/SeedVC电脑对照')
OUT.mkdir(exist_ok=True)
INPUT=OUT/'inputs'; INPUT.mkdir(exist_ok=True)
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
os.chdir(ROOT)
sys.path.insert(0,str(ROOT))
torch.set_num_threads(4)
torch.manual_seed(20261003)

def main():
    assets=json.loads((PINNED/'manifest.json').read_text(encoding='utf-8'))
    if len(assets)!=4 or any('error' in x for x in assets): raise RuntimeError('Incomplete assets')
    file_map={}
    for repo in assets:
        for item in repo['files']:
            if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()!=item['sha256']: raise RuntimeError('Asset hash mismatch')
            file_map[(repo['repository'],Path(item['path']).name)]=item['path']
    import hf_utils
    def pinned_load(repo_id,model_filename='pytorch_model.bin',config_filename=None):
        model=file_map[(repo_id,model_filename)]
        return (model,file_map[(repo_id,config_filename)]) if config_filename else model
    hf_utils.load_custom_model_from_hf=pinned_load
    import modules.commons as commons
    upstream_checkpoint_loader=commons.load_checkpoint
    def checked_checkpoint_loader(model,optimizer,path,*args,**kwargs):
        state=torch.load(path,map_location='cpu',weights_only=True)['net']
        for name,network in model.items():
            source={key.removeprefix('module.'):value for key,value in state[name].items()}
            for key,value in network.named_parameters():
                if not value.requires_grad: continue
                if key not in source or source[key].shape!=value.shape:
                    raise RuntimeError('Learned parameter missing/mismatched: '+name+'/'+key)
        return upstream_checkpoint_loader(model,optimizer,path,*args,**kwargs)
    commons.load_checkpoint=checked_checkpoint_loader
    config=yaml.safe_load((ROOT/'configs/presets/config_dit_mel_seed_uvit_xlsr_tiny.yml').read_text(encoding='utf-8'))
    config['model_params']['speech_tokenizer']['name']=str(PINNED/'facebook__wav2vec2-xls-r-300m')
    config_path=OUT/'pinned_tiny_config.yml'
    config_path.write_text(yaml.safe_dump(config,allow_unicode=True),encoding='utf-8')
    target_orig=Path('D:/总进度/目标人物语音/Track 8.wav')
    x,sr=sf.read(target_orig,dtype='float32')
    if x.ndim==2: x=x.mean(axis=1)
    x=x[:sr*8]; x=x*.04/max(float(np.sqrt(np.mean(x*x))),1e-8)
    target=INPUT/'target_track8_first8s.wav'
    sf.write(target,x,sr,subtype='FLOAT')
    baseline=json.loads(Path('D:/总进度/目标人物分析/自动评估与改进/baseline_评估记录.json').read_text(encoding='utf-8'))
    sources=[x for x in baseline['files'] if x['label']=='ordinary_same_text' or x['label'].startswith('source_')]
    if len(sources)!=3: raise RuntimeError('Expected same-text TTS and two real voices')
    import inference
    original_loader=inference.load_models
    loaded=None; load_seconds=None; counts={}
    def cached_load(args):
        nonlocal loaded,load_seconds
        if loaded is None:
            t=time.perf_counter(); loaded=original_loader(args); torch.cuda.synchronize(); load_seconds=time.perf_counter()-t
            nets,semantic,f0,vocoder,campplus,*_=loaded
            counts.update({name:sum(p.numel() for p in model.parameters()) for name,model in nets.items()})
            counts['campplus']=sum(p.numel() for p in campplus.parameters())
            counts['vocoder']=sum(p.numel() for p in vocoder.parameters())
            for cell in semantic.__closure__ or []:
                value=cell.cell_contents
                if isinstance(value,torch.nn.Module): counts['semantic_encoder']=sum(p.numel() for p in value.parameters())
            print('Parameter counts '+json.dumps(counts),flush=True)
        return loaded
    inference.load_models=cached_load
    records=[]
    for source in sources:
        x,sr=sf.read(source['path'],dtype='float32')
        if x.ndim==2: x=x.mean(axis=1)
        x=x*.04/max(float(np.sqrt(np.mean(x*x))),1e-8)
        name='same_text' if source['label']=='ordinary_same_text' else source['label'].removeprefix('source_')
        normalized=INPUT/(name+'.wav'); sf.write(normalized,x,sr,subtype='FLOAT')
        for steps in [8,30]:
            torch.manual_seed(20261003); torch.cuda.reset_peak_memory_stats()
            args=SimpleNamespace(source=str(normalized),target=str(target),output=str(OUT),
                diffusion_steps=steps,length_adjust=1.0,inference_cfg_rate=.7,
                f0_condition=False,auto_f0_adjust=False,semi_tone_shift=0,
                checkpoint=file_map[('Plachta/Seed-VC','DiT_uvit_tat_xlsr_ema.pth')],
                config=str(config_path),fp16=True)
            print('CONVERT '+name+f' steps={steps}',flush=True)
            before=loaded is not None
            t=time.perf_counter(); inference.main(args); torch.cuda.synchronize(); elapsed=time.perf_counter()-t
            model_seconds=elapsed if before else elapsed-load_seconds
            dest=OUT/f'vc_{name}_{target.stem}_1.0_{steps}_0.7.wav'
            generated,rate=sf.read(dest,dtype='float32')
            if not np.isfinite(generated).all() or np.sqrt(np.mean(generated*generated))<1e-6: raise RuntimeError('Invalid output')
            row=dict(label=f'seed_tiny_steps{steps}_{name}',group=f'seed_tiny_steps{steps}',path=str(dest),
                test_name=name,expected_text=source['expected_text'],text_origin=source['text_origin'],
                source_path=source['path'],normalized_input=str(normalized),
                source_sha256=hashlib.sha256(Path(source['path']).read_bytes()).hexdigest(),
                sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
                target_reference=str(target),target_reference_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                source_seconds=len(x)/sr,output_seconds=len(generated)/rate,peak=float(np.max(np.abs(generated))),
                clipped_fraction=float(np.mean(np.abs(generated)>=.9999)),
                model_inference_seconds_excluding_initial_load=model_seconds,
                approximate_pc_rtf=model_seconds/(len(generated)/rate),
                peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),
                seed=20261003,board_deployed=False,causal_streaming=False,source_speaker_enrollment=False)
            if name=='same_text': row['same_text_target']='D:/总进度/目标人物分析/素材同文本普通声转换对比/目标人物原声_试听.wav'
            records.append(row)
            (OUT/'SeedVC对照音频记录.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    report=dict(status='complete',source_revision='51383efd921027683c89e5348211d93ff12ac2a8',
        local_change='Move optional DAC import into vector_quantize branch; selected configuration does not use it.',
        model_assets=assets,parameter_counts=counts,initial_load_seconds=load_seconds,
        audio_uploaded=False,board_deployed=False,subjective_acceptance=False,
        reference_original=str(target_orig),reference_original_sha256=hashlib.sha256(target_orig.read_bytes()).hexdigest(),
        target_reference_seconds=8,weights_finetuned=False,
        timing_note='PC offline full-utterance conversion; approximate RTF is not live or board end-to-end latency.',files=records)
    (OUT/'运行记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('COMPLETE '+str(OUT),flush=True)

if __name__=='__main__': main()
