"""Extract exact deployed C features for source/teacher training, plus codec controls."""
from train_board_student_20261005 import BASE,CORPUS,read
from pathlib import Path
import numpy as np,json,subprocess,soundfile as sf
native=BASE.parent/'board_support/native_llvc_20261005';budget=BASE.parent/'board_budget_20261005'
out=budget/'fargan_corpus';out.mkdir(exist_ok=True);exe=str(native/'fargan_probe_host.exe')
doc=json.loads((CORPUS/'paired_manifest.json').read_text(encoding='utf-8'));rows=[]
controls={kind:[] for kind in ['fargan_source_reconstruction','fargan_teacher_reconstruction']}
def extract(path,stem):
 x=read(path);pcm=np.rint(np.clip(x,-1,32767/32768)*32768).astype('<i2');raw=out/(stem+'.pcm');pcm.tofile(raw)
 features=out/(stem+'.features.f32');stats=out/(stem+'.features.json')
 subprocess.run([exe,'--features',str(raw),str(features),str(stats)],check=True)
 f=np.fromfile(features,dtype=np.float32).reshape(-1,20);assert np.isfinite(f).all()
 return features,raw,len(x)
for row in [r for r in doc['files'] if r['split']!='test']:
 stem=Path(row['filename']).stem;source,raw,n=extract(row['path'],stem+'_source');teacher,traw,tn=extract(row['teacher_path'],stem+'_teacher')
 rows.append(dict(row,source_features=str(source),teacher_features=str(teacher),source_samples=n,teacher_samples=tn))
 if row['split']=='validation':
  for kind,features in [('fargan_source_reconstruction',source),('fargan_teacher_reconstruction',teacher)]:
   dest=out/(stem+'_'+kind+'.pcm');subprocess.run([exe,'--synthesis',str(features),str(dest),str(out/(stem+'_'+kind+'.json'))],check=True)
   y=np.fromfile(dest,dtype='<i2').astype('float32')/32768;wav=budget/kind/(stem+'_student.wav');wav.parent.mkdir(exist_ok=True);sf.write(wav,y,16000,subtype='FLOAT')
   controls[kind].append(dict(row,student_path=str(wav)))
 print('FEATURES',stem,row['split'],flush=True)
targets=[]
for i in range(5,9):
 path=Path('D:/总进度/目标人物语音')/('Track '+str(i)+'.wav');f,raw,n=extract(path,'target_track'+str(i));targets.append(dict(path=str(path),features=str(f),samples=n))
(out/'manifest.json').write_text(json.dumps(dict(complete=True,files=rows,target_training=targets,test_audio_used=False,target_track9_used=False,source_enrollment=False,feature_dim=20,frame_samples=160,official_pretrained_vocoder=True),ensure_ascii=False,indent=2),encoding='utf-8')
for kind,outputs in controls.items():
 (budget/kind/'decision.json').write_text(json.dumps(dict(complete=True,heldout_outputs=outputs,control_only=True,target_voice_conversion=False,source_enrollment=False,recognizer_used_as_loss=False,auxiliary_speaker_loss_used=False),ensure_ascii=False,indent=2),encoding='utf-8')
print('FARGAN_FEATURES_READY',flush=True)
