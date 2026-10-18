"""Offline cache of the exact causal deployment preprocessor; no oracle F0."""
from train_board_student_20261005 import BASE,CORPUS,read
from pathlib import Path
import subprocess,json,numpy as np,hashlib,soundfile as sf
native=BASE.parent/'board_support/native_llvc_20261005'
out=BASE.parent/'board_budget_20261005/causal_pitch_corpus';out.mkdir(exist_ok=True)
rows=json.loads((CORPUS/'paired_manifest.json').read_text(encoding='utf-8'))['files'];records=[]
for row in [r for r in rows if r['split']!='test']:
 stem=Path(row['filename']).stem;x=read(row['path']);inp=out/(stem+'.in.f32');shift=out/(stem+'.pitch.f32');stats=out/(stem+'.pitch.json');x.tofile(inp)
 subprocess.run([str(native/'causal_pitch_normalizer_host.exe'),str(inp),str(shift),str(stats)],check=True,capture_output=True)
 y=np.fromfile(shift,dtype=np.float32);assert len(y)==len(x) and np.isfinite(y).all();wav=out/(stem+'_pitched.wav');sf.write(wav,y,16000,subtype='FLOAT')
 records.append(dict(row,pitch_source_path=str(wav),pitch_wave_sha256=hashlib.sha256(wav.read_bytes()).hexdigest(),pitch_stats=json.loads(stats.read_text())))
print('PITCH_CORPUS_PREPARED',len(records),flush=True)
(out/'manifest.json').write_text(json.dumps(dict(complete=True,files=records,host_executable_sha256=hashlib.sha256((native/'causal_pitch_normalizer_host.exe').read_bytes()).hexdigest(),target_pitch_hz=193.13304493,target_tracks='5-8',test_audio_used=False,source_speaker_enrollment=False,future_source_statistics_used=False),ensure_ascii=False,indent=2),encoding='utf-8')
source=(BASE/'train_board_wide_shallow_target_anchor_20261005.py').read_text(encoding='utf-8')
source=source.replace("OUT=BASE.parent/'board_budget_20261005/wide192_shallow2_target_anchor'","OUT=BASE.parent/'board_budget_20261005/wide192_causal_pitch_trained'")
source=source.replace("PARENT=BASE.parent/'board_budget_20261005/wide192_shallow2_reconstruction_refined/checkpoint_step3200.pt'","PARENT=BASE.parent/'board_budget_20261005/wide192_shallow2_target_anchor/checkpoint_step800.pt'")
source=source.replace("doc=json.loads((CORPUS/'paired_manifest.json').read_text(encoding='utf-8'))","doc=json.loads((BASE.parent/'board_budget_20261005/causal_pitch_corpus/manifest.json').read_text(encoding='utf-8'))")
source=source.replace("x,y=read(row['path']),read(row['teacher_path'])","x,y=read(row['pitch_source_path']),read(row['teacher_path'])")
# Keep original clean speech for CTC guidance, rather than deriving labels from DSP distortions.
source=source.replace("data.append((torch.tensor(x,device=device),torch.tensor(y,device=device)))","data.append((torch.tensor(x,device=device),torch.tensor(y,device=device),torch.tensor(read(row['path']),device=device)))")
source=source.replace("x,y=data[int(rng.integers(len(data)))];xx,at=crop(x);yy,_=crop(y,at);clean.append(xx)","x,y,original=data[int(rng.integers(len(data)))];xx,at=crop(x);yy,_=crop(y,at);cc,_=crop(original,at);clean.append(cc)")
source=source.replace("x=read(row['path']);y=stream(model,x)","x=read(row['pitch_source_path']);y=stream(model,x)")
source=source.replace("wide192_shallow2_target_anchor.f32","wide192_causal_pitch_trained.f32")
source=source.replace("runtime_no_original_mix=True,discriminator_rms_normalization=.1","runtime_no_original_mix=True,causal_pitch_preprocessing=True,target_pitch_hz=193.13304493,prior_conversion_steps=800,discriminator_rms_normalization=.1")
source=source.replace("from train_board_student_20261005 import BASE,CORPUS,build_small,export,stream,read,Objective,PeriodDiscriminator","from train_board_student_20261005 import BASE,CORPUS,build_small,export,stream,read,Objective,PeriodDiscriminator\n# This phase fine-tunes an actual causal pitch-preprocessed training corpus.")
(BASE/'train_board_wide_causal_pitch_20261006.py').write_text(source,encoding='utf-8')
