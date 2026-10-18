"""Alternative target-conditioning controls on frozen source/target material."""
from pathlib import Path
import hashlib,json,os,sys,time
import run_rvc_pilot as pilot
pilot.settings()
import numpy as np
import soundfile as sf
import torch
from scipy.signal import resample_poly
from math import gcd
BASE=Path(__file__).resolve().parent;ROOT=BASE/'Seed-VC'
OUT=Path('D:/总进度/目标人物分析/音色与自然度复查');OUT.mkdir(parents=True,exist_ok=True)
os.chdir(ROOT);sys.path.insert(0,str(ROOT));torch.set_num_threads(4)
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
assets=read(ROOT/'checkpoints/pinned/training_manifest.json')
repo=next(r for r in assets if r['repository']=='myshell-ai/OpenVoiceV2')
for r in repo['files']:assert sha(r['path'])==r['sha256']
from modules.openvoice.api import ToneColorConverter
folder=Path(repo['local'])
model=ToneColorConverter(str(folder/'converter/config.json'),device='cuda:0')
state=torch.load(folder/'converter/checkpoint.pth',map_location='cpu',weights_only=True)['model']
model.model.load_state_dict(state,strict=True);model.model.eval().requires_grad_(False);del state

def audio(path):
    x,sr=sf.read(path,dtype='float32')
    if x.ndim==2:x=x.mean(axis=1)
    divisor=gcd(sr,22050);x=resample_poly(x,22050//divisor,sr//divisor).astype(np.float32)
    x=x*.04/max(float(np.sqrt(np.mean(x*x))),1e-8)
    return torch.from_numpy(x)[None].to('cuda'),torch.tensor([len(x)],device='cuda')

target_rows=[];target_embeddings=[]
for n in range(5,9):
    path=Path(f'D:/总进度/目标人物语音/Track {n}.wav');x,length=audio(path)
    target_embeddings.append(model.extract_se(x,length));target_rows.append(dict(path=str(path),sha256=sha(path)))
mean_embedding=torch.stack(target_embeddings).mean(0)
x,length=audio(Path('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav'))
t6_embedding=model.extract_se(x,length)
target_profiles={'mean4_tracks':mean_embedding,'track6_8s':t6_embedding}
baseline=read(Path('D:/总进度/目标人物分析/自动评估与改进/baseline_评估记录.json'))['files']
sources=[r for r in baseline if r['label']=='ordinary_same_text' or r['label'].startswith('source_')]
sources+=read(BASE/'public_chinese_validation/validation_manifest.json')['files']
sources+=read(OUT/'neural_control_manifest.json')['files']
records=[]
for reference_name,target in target_profiles.items():
    output_folder=OUT/('openvoice_'+reference_name);output_folder.mkdir(exist_ok=True)
    for row in sources:
        torch.manual_seed(20261003)
        x,length=audio(row['path']);start=time.perf_counter()
        current_embedding=model.extract_se(x,length)
        result=model.convert(x,length,current_embedding,target,tau=.3).squeeze().cpu().numpy()
        torch.cuda.synchronize();elapsed=time.perf_counter()-start
        name='same_text' if row['label']=='ordinary_same_text' else Path(row['path']).stem
        dest=output_folder/(name+'.wav');sf.write(dest,result,22050,subtype='PCM_24')
        assert np.isfinite(result).all() and np.sqrt(np.mean(result*result))>1e-6
        rec=dict(label='openvoice_'+reference_name+'_'+name,group='openvoice_'+reference_name,test_name=name,
            path=str(dest),sha256=sha(dest),source_path=row['path'],source_sha256=sha(row['path']),
            expected_text=row['expected_text'],text_origin=row['text_origin'],seconds=len(result)/22050,
            reference_profile=reference_name,target_originals=target_rows,tau=.3,seed=20261003,
            automatic_source_embedding_from_current_audio=True,source_speaker_enrollment=False,causal_streaming=False,
            board_deployed=False,subjective_acceptance=False,offline_pc_file_seconds=elapsed)
        if name=='same_text' or row['label'].startswith('generic_neural_'):
            rec['same_text_target']='D:/总进度/目标人物分析/素材同文本普通声转换对比/目标人物原声_试听.wav'
        records.append(rec)
        (OUT/'openvoice_items.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
        print('OUTPUT '+rec['label'],flush=True)
(OUT/'openvoice_run.json').write_text(json.dumps(dict(status='complete',files=records,assets=repo,
    model_parameters=sum(p.numel() for p in model.model.parameters()),target_profile_method='equal average of unnormalized four utterance reference embeddings; alternative Track6 8s',
    audio_uploaded=False,weights_finetuned=False,board_deployed=False,causal_streaming=False,
    note='Current whole-clip source embedding is automatic, not enrollment, but not causal streaming. Pitch/prosody preservation may limit any-to-one identity.'),ensure_ascii=False,indent=2),encoding='utf-8')
print('OPENVOICE COMPLETE',flush=True)
