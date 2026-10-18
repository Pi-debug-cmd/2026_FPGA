"""Staged local pilot: speaker train/heldout split, features, training, export.
Only stages explicitly requested are run. Original recordings are unchanged.
This PC teacher baseline is not a Zynq deployment.
"""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys, wave

BASE=Path(__file__).resolve().parent
ROOT=BASE/'RVC'
DATA=BASE/'target_pilot_data'
EXP=ROOT/'logs'/'target_person_pilot'
ORIGINAL=Path('D:/总进度/目标人物语音')

def settings():
    for key,value in {
        'TMP':'D:/Tools_codex/temp', 'TEMP':'D:/Tools_codex/temp',
        'HF_HOME':str(BASE/'cache'/'hf'), 'TORCH_HOME':str(BASE/'cache'/'torch'),
        'MPLCONFIGDIR':str(BASE/'cache'/'matplotlib'),
        'NUMBA_CACHE_DIR':str(BASE/'cache'/'numba'),
        'XDG_CACHE_HOME':str(BASE/'cache'),
        'PYTHONPATH':str(ROOT), 'PYTHONUTF8':'1',
        'weight_root':str(ROOT/'assets'/'weights'),
        'rmvpe_root':str(ROOT/'assets'/'rmvpe'),
        'index_root':str(ROOT/'logs'),
        'outside_index_root':str(ROOT/'assets'/'indices'),
    }.items():
        os.environ[key]=value
    os.environ['PATH']=str(ROOT)+os.pathsep+os.environ.get('PATH','')
    (ROOT/'assets'/'weights').mkdir(parents=True,exist_ok=True)
    EXP.mkdir(parents=True,exist_ok=True)

def command(stage,*args):
    print('Stage: '+stage,flush=True)
    log=EXP/(stage+'.console.log')
    with log.open('w',encoding='utf-8') as output:
        result=subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,
                              stdout=output,stderr=subprocess.STDOUT)
    if result.returncode:
        print(log.read_text(encoding='utf-8',errors='replace')[-7000:])
        raise RuntimeError(f'{stage} failed ({result.returncode}); log={log}')
    print('Completed: '+stage,flush=True)

def prepare():
    records=[]
    for number in range(5,10):
        original=ORIGINAL/f'Track {number}.wav'
        split='heldout' if number==9 else 'train'
        copy=DATA/split/original.name
        if not copy.is_file():
            raise FileNotFoundError(copy)
        digest=hashlib.sha256(original.read_bytes()).hexdigest()
        if hashlib.sha256(copy.read_bytes()).hexdigest()!=digest:
            raise RuntimeError('Original-copy mismatch: '+str(copy))
        with wave.open(str(original),'rb') as wav:
            duration=wav.getnframes()/wav.getframerate()
        records.append(dict(original=str(original),copy=str(copy),split=split,
                            seconds=duration,sha256=digest))
    (DATA/'split_manifest.json').write_text(json.dumps(dict(
        purpose='Target-person teacher pilot; heldout never used for training/index',
        files=records),ensure_ascii=False,indent=2),encoding='utf-8')
    cfg=json.loads((ROOT/'configs'/'v1'/'40k.json').read_text())
    cfg['train']['log_interval']=20
    (EXP/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    print('Prepared train 5-8 / heldout 9; source hashes verified.',flush=True)

def features():
    command('preprocess','-m','train.preprocess',DATA/'train',40000,1,EXP,'True',3.7)
    command('f0','-m','train.dataset.extract_f0','cuda',1,0,0,EXP,'True')
    command('hubert','-m','train.dataset.extract_hubert_feature','cuda:0',1,0,EXP,'v2','True')
    import numpy as np
    import soundfile as sf
    # Two 3-second silence entries, matching the author pipeline's mute examples.
    # No speech from heldout enters these examples.
    for folder in ['0_gt_wavs','3_feature768','2a_f0','2b-f0nsf']:
        (EXP/folder).mkdir(exist_ok=True)
    sf.write(EXP/'0_gt_wavs'/'pilot_mute.wav',np.zeros(120000),40000,subtype='PCM_16')
    np.save(EXP/'3_feature768'/'pilot_mute.npy',np.zeros((150,768),dtype=np.float32))
    np.save(EXP/'2a_f0'/'pilot_mute.wav.npy',np.ones(300,dtype=np.int64))
    np.save(EXP/'2b-f0nsf'/'pilot_mute.wav.npy',np.zeros(300,dtype=np.float32))
    lines=[]
    for audio in sorted((EXP/'0_gt_wavs').glob('*.wav')):
        name=audio.stem
        paths=[audio,EXP/'3_feature768'/(name+'.npy'),
               EXP/'2a_f0'/(name+'.wav.npy'),EXP/'2b-f0nsf'/(name+'.wav.npy')]
        for path in paths:
            if not path.is_file(): raise FileNotFoundError(path)
        line='|'.join(p.as_posix() for p in paths)+'|0'
        lines.extend([line]* (2 if name=='pilot_mute' else 1))
    if len(lines)<4: raise RuntimeError('Insufficient processed segments')
    (EXP/'filelist.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Validated training filelist with {len(lines)} entries.',flush=True)

def train(epochs):
    if not (EXP/'filelist.txt').is_file(): raise RuntimeError('Run feature stage first')
    command(f'train_{epochs}',BASE/'train_rvc_low_memory.py','-e',EXP.name,
            '-sr','40k','-f0',1,'-bs',2,'-g',0,'-te',epochs,
            '-se',min(10,epochs),'-pg','assets/pretrained_v2/f0G40k.pth',
            '-pd','assets/pretrained_v2/f0D40k.pth','-l',1,'-c',0,'-sw',1,'-v','v2')

def preview():
    import numpy as np
    import soundfile as sf
    out=Path('D:/总进度/目标人物分析/音色模型首次试训')
    out.mkdir(parents=True,exist_ok=True)
    model=ROOT/'assets'/'weights'/'target_person_pilot.pth'
    if not model.is_file(): raise FileNotFoundError(model)
    sample=BASE/'LLVC'/'test_wavs'/'174-50561-0000.wav'
    audio,sr=sf.read(sample)
    sf.write(out/'公开英语测试_转换前.wav',audio,sr,subtype='PCM_16')
    # Public source utterance is not the user's speech and not in target training.
    for pitch in [0,6]:
        command(f'preview_pitch{pitch}','-m','infer.cli','--model',model,
                '--input',sample,'--output',out/f'公开英语测试_目标模型_升{pitch}半音.wav',
                '--pitch',pitch,'--speaker-id',0,'--index-rate',0.75)
    command('heldout_roundtrip','-m','infer.cli','--model',model,
            '--input',DATA/'heldout'/'Track 9.wav',
            '--output',out/'目标人物留出录音_模型重建.wav',
            '--pitch',0,'--speaker-id',0,'--index-rate',0.75)
    results=[]
    for path in sorted(out.glob('*.wav')):
        if path.stem.endswith('_音量对齐'): continue
        x,rate=sf.read(path)
        if not np.isfinite(x).all() or np.max(np.abs(x))==0:
            raise RuntimeError('Nonfinite or silent output: '+str(path))
        results.append(dict(path=str(path),sr=rate,seconds=len(x)/rate,
                            peak=float(np.max(np.abs(x))),rms=float(np.sqrt(np.mean(x*x)))))
        # Match RMS without clipping so loudness does not masquerade as timbre.
        gain=min(0.04/float(np.sqrt(np.mean(x*x))),0.95/float(np.max(np.abs(x))))
        sf.write(path.with_name(path.stem+'_音量对齐.wav'),x*gain,rate,subtype='PCM_16')
    (out/'试听文件检查.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Preview files numerically checked; human listening still required.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('stage',choices=['prepare','features','train','preview'])
    p.add_argument('--epochs',type=int,default=20)
    p.add_argument('--experiment',default='target_person_pilot',
                   choices=['target_person_pilot','target_person_corrected'])
    args=p.parse_args()
    EXP=ROOT/'logs'/args.experiment
    if args.stage=='preview' and args.experiment!='target_person_pilot':
        p.error('legacy English preview only supports the original experiment')
    settings()
    if args.stage=='prepare': prepare()
    elif args.stage=='features': features()
    elif args.stage=='train': train(args.epochs)
    else: preview()
