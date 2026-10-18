"""Full-width controls distinguish codec compression from deployment numerics.
Neither control is an accepted target model or a board real-time result.
"""
from train_board_student_20261005 import BASE,CORPUS,stream,read
from load_llvc_audit_model import load_model
from pathlib import Path
import torch,json,numpy as np,soundfile as sf,argparse
parser=argparse.ArgumentParser();parser.add_argument('--kind',choices=['full512_official','full512_targetpilot']);args=parser.parse_args()
torch.set_num_threads(4)
budget=BASE.parent/'board_budget_20261005'
rows=json.loads((CORPUS/'paired_manifest.json').read_text(encoding='utf-8'))['files']
for kind in ([args.kind] if args.kind else ['full512_official','full512_targetpilot']):
 out=budget/kind;out.mkdir(exist_ok=True)
 model,cfg=load_model(True)
 if kind=='full512_targetpilot':model.load_state_dict(torch.load(BASE.parent/'board_budget_20261004/phasefree_student_pilot/checkpoint_step20.pt',map_location='cpu',weights_only=True)['model'],strict=True)
 model.eval();outputs=[]
 for row in [r for r in rows if r['split']=='validation']:
  y=stream(model,read(row['path']));p=out/(Path(row['filename']).stem+'_student.wav');sf.write(p,y,16000,subtype='FLOAT')
  outputs.append(dict(row,student_path=str(p),rms=float(np.sqrt(np.mean(y*y))),peak=float(np.max(np.abs(y)))))
  print('FULL_CONTROL',kind,row['filename'],flush=True)
 (out/'decision.json').write_text(json.dumps(dict(complete=True,heldout_outputs=outputs,quality_accepted=False,board_real_time=False,recognizer_used_as_loss=False,auxiliary_speaker_loss_used=False,scope='full-width control, not accepted target voice'),ensure_ascii=False,indent=2),encoding='utf-8')
