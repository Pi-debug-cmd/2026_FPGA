"""Render a recorded training prefix for development screening, no test search."""
from train_board_student_20261005 import BASE,CORPUS,build_small,export,stream,read
from pathlib import Path
import argparse,json,hashlib
import numpy as np,torch,soundfile as sf
parser=argparse.ArgumentParser();parser.add_argument('--step',type=int,required=True);args=parser.parse_args()
assert args.step in [400,800,1200,1600,2000,2400]
torch.set_num_threads(4)
parent=BASE.parent/'board_budget_20261005/small128_target_anchor'
out=BASE.parent/'board_budget_20261005'/('small128_target_anchor_step'+str(args.step));out.mkdir(exist_ok=True)
checkpoint=parent/('checkpoint_step'+str(args.step)+'.pt')
model,cfg,selection=build_small(128);state=torch.load(checkpoint,map_location='cpu',weights_only=True)
assert state['steps']==args.step and not state['target_track9_used_for_training']
model.load_state_dict(state['model'],strict=True);model.eval();export(model,out/'small128_target_anchor.f32')
rows=json.loads((CORPUS/'paired_manifest.json').read_text(encoding='utf-8'))['files'];outputs=[]
for row in [r for r in rows if r['split']=='validation']:
 x=read(row['path']);y=stream(model,x);p=out/(Path(row['filename']).stem+'_student.wav');sf.write(p,y,16000,subtype='FLOAT')
 outputs.append(dict(row,student_path=str(p),rms=float(np.sqrt(np.mean(y*y))),peak=float(np.max(np.abs(y)))))
report=dict(complete=True,heldout_outputs=outputs,steps=args.step,reconstruction_steps=800,config=cfg,parameters=sum(p.numel() for p in model.parameters()),checkpoint_path=str(checkpoint),checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),weights_sha256=hashlib.sha256((out/'small128_target_anchor.f32').read_bytes()).hexdigest(),recognizer_used_as_loss=True,auxiliary_speaker_loss_used=True,target_track9_used_for_training=False,validation_reused_for_development=True,test_not_rendered_or_searched=True,source_enrollment=False,quality_accepted=False,board_live_verified=False)
(out/'decision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('PREFIX_RENDERED',str(out),flush=True)
