from train_board_student_20261005 import BASE,read
from audit_wide_pitch_profiles_20261005 import profile
from pathlib import Path
import json,parselmouth,numpy as np
out=BASE.parent/'board_budget_20261005/wide192_causal_pitch_initial'
doc=json.loads((out/'decision.json').read_text(encoding='utf-8'));records=[]
for row in doc['heldout_outputs']:
 r=dict(filename=row['filename'],source=profile(row['path']),teacher=profile(row['teacher_path']),pitched=profile(row['pitch_source_path']),student=profile(row['student_path']))
 records.append(r);print('PITCH_CANDIDATE',row['filename'],[(k,r[k]['f0_percentiles_hz']) for k in ['source','teacher','pitched','student']],flush=True)
targets=[]
for i in range(5,9):
 p=Path('D:/总进度/目标人物语音')/('Track '+str(i)+'.wav');x=read(p)
 f=parselmouth.Sound(x,16000).to_pitch_ac(time_step=.01,pitch_floor=60,pitch_ceiling=600,voicing_threshold=.5).selected_array['frequency'];targets.extend(f[f>0])
print('TARGET_POOL',np.percentile(targets,[10,50,90]),flush=True)
(out/'pitch_profiles.json').write_text(json.dumps(dict(cases=records,target_tracks5_8_percentiles=np.percentile(targets,[10,50,90]).tolist(),not_identity_approval=True),ensure_ascii=False,indent=2),encoding='utf-8')
