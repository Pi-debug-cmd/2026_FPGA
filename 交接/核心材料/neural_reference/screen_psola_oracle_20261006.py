"""Offline whole-recording oracle control, explicitly NOT board/causal deployment."""
from train_board_student_20261005 import BASE,read
from pathlib import Path
import json,numpy as np,parselmouth,soundfile as sf
from parselmouth.praat import call
budget=BASE.parent/'board_budget_20261005';out=budget/'wide192_psola_oracle';out.mkdir(exist_ok=True)
parent=budget/'wide192_shallow2_target_anchor';doc=json.loads((parent/'decision.json').read_text(encoding='utf-8'));rows=[]
for row in doc['heldout_outputs']:
 x=read(row['student_path']);sound=parselmouth.Sound(x,16000)
 pitch=sound.to_pitch_ac(time_step=.01,pitch_floor=60,pitch_ceiling=600,voicing_threshold=.5);freq=pitch.selected_array['frequency'];center=float(np.median(freq[freq>0]));ratio=float(np.clip(193.13304493/center,.65,2.2))
 manipulation=call(sound,'To Manipulation',.01,60,600);tier=call(manipulation,'Extract pitch tier');call(tier,'Multiply frequencies',0,len(x)/16000,ratio);call([tier,manipulation],'Replace pitch tier')
 synthesized=call(manipulation,'Get resynthesis (overlap-add)');y=synthesized.values[0].astype('float32');assert len(y)==len(x)
 path=out/(Path(row['filename']).stem+'_student.wav');sf.write(path,y,16000,subtype='FLOAT');rows.append(dict(row,student_path=str(path),source_pitch_median_hz=center,pitch_ratio=ratio))
 print('ORACLE_PSOLA',row['filename'],ratio,flush=True)
(out/'decision.json').write_text(json.dumps(dict(complete=True,heldout_outputs=rows,not_causal=True,whole_recording_source_statistics=True,praat_control_only=True,source_enrollment=False,recognizer_used_as_loss=True,auxiliary_speaker_loss_used=True,quality_accepted=False,not_board_deployable=True),ensure_ascii=False,indent=2),encoding='utf-8')
