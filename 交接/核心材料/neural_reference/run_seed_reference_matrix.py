"""Controlled reference/model tests; no source speaker enrollment or board writes."""
from pathlib import Path
from types import SimpleNamespace
import argparse,hashlib,json,os,sys,time
import numpy as np
import soundfile as sf
import torch
import yaml
import run_rvc_pilot as pilot
pilot.settings()
BASE=Path(__file__).resolve().parent; ROOT=BASE/'Seed-VC'; PINNED=ROOT/'checkpoints/pinned'
OUT=Path('D:/总进度/目标人物分析/SeedVC下一阶段')
os.environ['HF_HUB_OFFLINE']='1'; os.environ['TRANSFORMERS_OFFLINE']='1'
os.chdir(ROOT); sys.path.insert(0,str(ROOT)); torch.set_num_threads(4)

def prepare_references():
    folder=OUT/'inputs'; folder.mkdir(parents=True,exist_ok=True)
    records={}; pool=[]
    for number in range(5,9):
        original=Path(f'D:/总进度/目标人物语音/Track {number}.wav')
        x,sr=sf.read(original,dtype='float32')
        if x.ndim==2: x=x.mean(axis=1)
        clip=x[:sr*8]; clip=clip*.04/max(float(np.sqrt(np.mean(clip*clip))),1e-8)
        path=folder/f'target_t{number}_8s.wav'; sf.write(path,clip,sr,subtype='FLOAT')
        records[f't{number}_8s']=dict(path=str(path),seconds=len(clip)/sr,original=str(original),original_sha256=hashlib.sha256(original.read_bytes()).hexdigest())
        pool.append(clip[:sr*6])
    pooled=np.concatenate(pool); path=folder/'target_pool24s.wav'; sf.write(path,pooled,sr,subtype='FLOAT')
    records['pool24s']=dict(path=str(path),seconds=len(pooled)/sr,segments=[dict(track=n,start=0,seconds=6) for n in range(5,9)],note='Discontinuous diagnostic reference, not a new recording')
    for row in records.values(): row['sha256']=hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()
    (OUT/'参考片段清单.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    return records

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--model',choices=['tiny','strong'],required=True)
    parser.add_argument('--refs',default='t5_8s,t6_8s,t7_8s,t8_8s,pool24s'); parser.add_argument('--steps',type=int,default=30)
    parser.add_argument('--source-manifest',type=Path); parser.add_argument('--tag',default='')
    args=parser.parse_args(); references=prepare_references()
    assets=json.loads((PINNED/'manifest.json').read_text(encoding='utf-8'))
    if args.model=='strong': assets+=json.loads((PINNED/'strong_manifest.json').read_text(encoding='utf-8'))
    file_map={}
    for repo in assets:
        for row in repo['files']:
            if hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()!=row['sha256']: raise RuntimeError('Weight SHA mismatch')
            file_map[(repo['repository'],Path(row['path']).name)]=row['path']
    import hf_utils
    hf_utils.load_custom_model_from_hf=lambda repo_id,model_filename='pytorch_model.bin',config_filename=None: file_map[(repo_id,model_filename)] if config_filename is None else (file_map[(repo_id,model_filename)],file_map[(repo_id,config_filename)])
    import modules.commons as commons
    upstream=commons.load_checkpoint
    def checked_load(model,optimizer,path,*arguments,**kwargs):
        state=torch.load(path,map_location='cpu',weights_only=True)['net']
        for name,network in model.items():
            source={k.removeprefix('module.'):v for k,v in state[name].items()}
            for key,value in network.named_parameters():
                if value.requires_grad and (key not in source or source[key].shape!=value.shape): raise RuntimeError('Missing/mismatched learned parameter '+name+'/'+key)
        return upstream(model,optimizer,path,*arguments,**kwargs)
    commons.load_checkpoint=checked_load
    preset='config_dit_mel_seed_uvit_xlsr_tiny.yml' if args.model=='tiny' else 'config_dit_mel_seed_uvit_whisper_small_wavenet.yml'
    config=yaml.safe_load((ROOT/'configs/presets'/preset).read_text(encoding='utf-8'))
    if args.model=='tiny':
        config['model_params']['speech_tokenizer']['name']=str(PINNED/'facebook__wav2vec2-xls-r-300m')
        checkpoint='DiT_uvit_tat_xlsr_ema.pth'
    else:
        config['model_params']['speech_tokenizer']['name']=str(BASE/'cache/hf/hub/models--openai--whisper-small/snapshots/973afd24965f72e36ca33b3055d56a652f456b4d')
        config['model_params']['vocoder']['name']=str(PINNED/'nvidia__bigvgan_v2_22khz_80band_256x')
        checkpoint='DiT_seed_v2_uvit_whisper_small_wavenet_bigvgan_pruned.pth'
    cfg_path=OUT/f'pinned_{args.model}_config.yml'; cfg_path.write_text(yaml.safe_dump(config,allow_unicode=True),encoding='utf-8')
    baseline=json.loads(Path('D:/总进度/目标人物分析/自动评估与改进/baseline_评估记录.json').read_text(encoding='utf-8'))
    sources=[x for x in baseline['files'] if x['label']=='ordinary_same_text' or x['label'].startswith('source_')]
    if args.source_manifest: sources=json.loads(args.source_manifest.read_text(encoding='utf-8'))['files']
    suffix=('_'+args.tag) if args.tag else ''
    import inference
    base_args=dict(diffusion_steps=args.steps,length_adjust=1.0,inference_cfg_rate=.7,f0_condition=False,
        auto_f0_adjust=False,semi_tone_shift=0,checkpoint=file_map[('Plachta/Seed-VC',checkpoint)],config=str(cfg_path),fp16=True)
    print('Loading '+args.model,flush=True); started=time.perf_counter()
    loaded=inference.load_models(SimpleNamespace(**base_args)); torch.cuda.synchronize(); load_seconds=time.perf_counter()-started
    counts={name:sum(p.numel() for p in network.parameters()) for name,network in loaded[0].items()}
    counts['campplus']=sum(p.numel() for p in loaded[4].parameters()); counts['vocoder']=sum(p.numel() for p in loaded[3].parameters())
    for cell in loaded[1].__closure__ or []:
        value=cell.cell_contents
        if isinstance(value,torch.nn.Module): counts['semantic_encoder']=sum(p.numel() for p in value.parameters())
    inference.load_models=lambda _:loaded
    records=[]
    for ref_name in args.refs.split(','):
        reference=references[ref_name]; folder=OUT/(args.model+'_'+ref_name+suffix); folder.mkdir(exist_ok=True)
        for source in sources:
            x,sr=sf.read(source['path'],dtype='float32')
            if x.ndim==2: x=x.mean(axis=1)
            x=x*.04/max(float(np.sqrt(np.mean(x*x))),1e-8)
            name='same_text' if source['label']=='ordinary_same_text' else source['label'].removeprefix('source_')
            if args.source_manifest: name=Path(source['path']).stem
            path=OUT/'inputs'/(name+'.wav'); sf.write(path,x,sr,subtype='FLOAT')
            torch.manual_seed(20261003); torch.cuda.reset_peak_memory_stats(); torch.cuda.synchronize()
            print('CONVERT '+args.model+' '+ref_name+' '+name,flush=True)
            started=time.perf_counter(); inference.main(SimpleNamespace(**base_args,source=str(path),target=reference['path'],output=str(folder)))
            torch.cuda.synchronize(); elapsed=time.perf_counter()-started
            dest=folder/f'vc_{name}_{Path(reference["path"]).stem}_1.0_{args.steps}_0.7.wav'
            audio,rate=sf.read(dest,dtype='float32')
            if not np.isfinite(audio).all() or np.sqrt(np.mean(audio*audio))<1e-6: raise RuntimeError('Invalid output')
            record=dict(label=f'seed_{args.model}_{ref_name}_steps{args.steps}{suffix}_{name}',group=f'seed_{args.model}_{ref_name}_steps{args.steps}{suffix}',
                path=str(dest),test_name=name,model_variant=args.model,reference_name=ref_name,reference=reference,
                source_path=source['path'],source_sha256=hashlib.sha256(Path(source['path']).read_bytes()).hexdigest(),
                source_gender_metadata=source.get('gender_metadata'),source_identity_metadata=source.get('speaker_identity_metadata'),
                expected_text=source['expected_text'],text_origin=source['text_origin'],sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
                seconds=len(audio)/rate,peak=float(np.max(np.abs(audio))),clipped_fraction=float(np.mean(np.abs(audio)>=.9999)),
                offline_file_seconds=elapsed,offline_pc_rtf=elapsed/(len(audio)/rate),peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),
                source_speaker_enrollment=False,board_deployed=False,causal_streaming=False,seed=20261003)
            if name=='same_text': record['same_text_target']='D:/总进度/目标人物分析/素材同文本普通声转换对比/目标人物原声_试听.wav'
            records.append(record)
            (OUT/f'{args.model}{suffix}_items.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    report=dict(status='complete',model=args.model,parameter_counts=counts,initial_load_seconds=load_seconds,assets=assets,
        source_revision='51383efd921027683c89e5348211d93ff12ac2a8',config=str(cfg_path),config_sha256=hashlib.sha256(cfg_path.read_bytes()).hexdigest(),
        audio_uploaded=False,board_deployed=False,subjective_acceptance=False,weights_finetuned=False,files=records)
    (OUT/f'{args.model}{suffix}_run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('COMPLETE '+str(OUT/f'{args.model}{suffix}_items.json'),flush=True)

if __name__=='__main__': main()
