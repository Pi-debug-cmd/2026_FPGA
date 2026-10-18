"""Measured pitch profiles, not a perceptual similarity or acceptance score."""
from train_board_student_20261005 import BASE,read
from pathlib import Path
import parselmouth,numpy as np,json
budget=BASE.parent/'board_budget_20261005';out=budget/'wide192_shallow2_target_anchor'
decision=json.loads((out/'decision.json').read_text(encoding='utf-8'))
def profile(path):
 x=read(path);pitch=parselmouth.Sound(x,16000).to_pitch_ac(time_step=.01,pitch_floor=60,pitch_ceiling=600,voicing_threshold=.5)
 f=pitch.selected_array['frequency'];voiced=f[f>0]
 return dict(path=str(path),voiced_frames=int(len(voiced)),total_frames=len(f),f0_percentiles_hz=np.percentile(voiced,[10,50,90]).tolist() if len(voiced) else None)
target=profile('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav');records=[]
for row in decision['heldout_outputs']:
 records.append(dict(filename=row['filename'],source=profile(row['path']),teacher=profile(row['teacher_path']),student=profile(row['student_path'])))
 print('PITCH',row['filename'],[(k,records[-1][k]['f0_percentiles_hz']) for k in ['source','teacher','student']],flush=True)
(out/'pitch_profiles.json').write_text(json.dumps(dict(target=target,cases=records,method='existing Praat autocorrelation, 10ms hop,60-600Hz,voicingthreshold0.5',not_quality_or_identity_approval=True),ensure_ascii=False,indent=2),encoding='utf-8')
