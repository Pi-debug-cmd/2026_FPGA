"""Apply the frozen RVC candidate to new inputs, without training/enrollment."""
from pathlib import Path
import hashlib,json,os,random,sys
import numpy as np
import soundfile as sf
import torch
import run_rvc_pilot as pilot
pilot.settings()
BASE=Path(__file__).resolve().parent; ROOT=BASE/'RVC'
OUT=Path('D:/总进度/目标人物分析/SeedVC下一阶段'); INPUT=OUT/'inputs'
DEST=OUT/'rvc_validation'; DEST.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT)); os.chdir(ROOT)
from infer.cli import create_config
from infer.vc.modules import VC
import pitch_conditioning_experiment as conditioning
sources=json.loads((BASE/'public_chinese_validation/validation_manifest.json').read_text(encoding='utf-8'))['files']
baseline=json.loads(Path('D:/总进度/目标人物分析/自动评估与改进/baseline_评估记录.json').read_text(encoding='utf-8'))
reference=baseline['target_reference_pitch']
center=float(np.median([np.log(x['median_hz']) for x in reference])); width=float(np.median([np.log(x['p90_hz']/x['p10_hz']) for x in reference]))
model=ROOT/'assets/weights/target_person_moretraining_e120_s1800.pth'; digest=hashlib.sha256(model.read_bytes()).hexdigest()
selected=json.loads(Path('D:/总进度/目标人物分析/自动评估与改进/当前自动候选.json').read_text(encoding='utf-8'))['selected']
if digest!=selected['model_sha256']: raise RuntimeError('Frozen candidate weight hash mismatch')
vc=VC(create_config()); vc.get_vc(model.name); conditioning.install(vc,'target_range',center,width)
index=next((ROOT/'logs/target_person_corrected').glob('added_IVF*_Flat_nprobe_1_*.index'))
rows=[]
for source in sources:
    original=Path(source['path']); x,sr=sf.read(original,dtype='float32')
    if x.ndim==2: x=x.mean(axis=1)
    x=x*.04/max(float(np.sqrt(np.mean(x*x))),1e-8)
    path=INPUT/(original.stem+'.wav'); sf.write(path,x,sr,subtype='FLOAT')
    random.seed(20261003); np.random.seed(20261003); torch.manual_seed(20261003)
    status,result=vc.vc_single(0,str(path),0,'rmvpe',str(index),.75,0,1.,.33)
    if not result or result[0] is None or result[1] is None: raise RuntimeError(status)
    rate,audio=result
    if np.issubdtype(audio.dtype,np.integer): audio=audio.astype('float64')/(np.iinfo(audio.dtype).max+1)
    if not np.isfinite(audio).all() or np.sqrt(np.mean(audio*audio))<1e-6: raise RuntimeError('Invalid output')
    audio=audio*min(.04/float(np.sqrt(np.mean(audio*audio))),.95/float(np.max(np.abs(audio))))
    dest=DEST/(original.stem+'.wav'); sf.write(dest,audio,rate,subtype='PCM_16')
    row=dict(label='rvc_e120_validation_'+original.stem,group='rvc_e120_target_range_validation',test_name=original.stem,
        path=str(dest),source_path=str(original),normalized_input=str(path),model=str(model),model_sha256=digest,
        expected_text=source['expected_text'],text_origin=source['text_origin'],source_gender_metadata=source['gender_metadata'],
        source_identity_metadata=source.get('speaker_identity_metadata'),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
        source_speaker_enrollment=False,board_deployed=False,causal_streaming=False,pitch_policy='whole_utterance_target_range')
    rows.append(row); print('Generated '+row['label'],flush=True)
(OUT/'rvc_validation_items.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print('COMPLETE frozen RVC new input tests',flush=True)
