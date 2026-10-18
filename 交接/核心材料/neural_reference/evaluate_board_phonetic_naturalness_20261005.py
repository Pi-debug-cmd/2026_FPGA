"""Independent UTMOS diagnostics for matched public validation audio.
Predicted naturalness is NOT Chinese pronunciation, identity or human acceptance.
"""
from pathlib import Path
import json,sys,hashlib,argparse,time
import torch,numpy as np
from run_rvc_pilot import settings
settings()
from train_board_student_20261005 import read
BASE=Path(__file__).resolve().parent;budget=BASE.parent/'board_budget_20261005';OUT=budget/'phonetic_naturalness';OUT.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--include-pilot',action='store_true');parser.add_argument('--candidate');args=parser.parse_args();torch.set_num_threads(4)
if args.candidate:assert args.candidate in ['small128_reconstruction','small128_target_anchor','full512_official','full512_targetpilot','wide192_shallow2_reconstruction','wide192_shallow2_reconstruction_refined','wide192_shallow2_target_anchor','wide192_causal_pitch_initial','wide192_causal_pitch_trained','wide192_psola_post','wide192_psola_oracle','fargan_source_reconstruction','fargan_teacher_reconstruction','fargan_mapper_v1','fargan_mapper_v2','fargan_cmn_direct','fargan_mapper_perceptual','fargan_mapper_truncated','fargan_mapper_pitchaware','fargan_teacher_source_energy','fargan_teacher_source_energy_periodicity','fargan_mapper_expanded_v8','fargan_v8_pitch_smooth','fargan_v8_source_voicing','fargan_v8_pitch_smooth_source_voicing','fargan_v8_dynamics','fargan_context_v9']+['small128_target_anchor_step'+str(s) for s in [400,800,1200,1600,2000,2400]]
manifest=json.loads((BASE/'cross_evaluators/manifest.json').read_text());asset=next(r for r in manifest if r['evaluator'].startswith('UTMOS'))
assert hashlib.sha256(Path(asset['weight']['path']).read_bytes()).hexdigest()==asset['weight']['sha256'];sys.path.insert(0,asset['source_directory'])
from speechmos.utmos22.strong.model import UTMOS22Strong
model=UTMOS22Strong();model.load_state_dict(torch.load(asset['weight']['path'],map_location='cpu',weights_only=True));model.eval();cache={}
cachepath=OUT/'cache.json'
if cachepath.exists():cache=json.loads(cachepath.read_text())
rows=json.loads((budget/'student_corpus/paired_manifest.json').read_text(encoding='utf-8'))['files'];records=[];begin=time.monotonic()
for row in [r for r in rows if r['split']=='validation']:
 sources=[('source',Path(row['path'])),('teacher',Path(row['teacher_path'])),('student6400',budget/'small96_identity_training'/(Path(row['filename']).stem+'_student.wav')),('student9200',budget/'small96_noise_refinement'/(Path(row['filename']).stem+'_student.wav'))]
 if args.include_pilot:sources.append(('phonetic_pilot',budget/'small96_phonetic_pilot'/(Path(row['filename']).stem+'_student.wav')))
 if args.candidate:sources.append((args.candidate,budget/args.candidate/(Path(row['filename']).stem+'_student.wav')))
 for kind,path in sources:
  digest=hashlib.sha256(path.read_bytes()).hexdigest();key=asset['weight']['sha256']+digest
  if key not in cache:
   x=read(path);clips=[];weights=[]
   for at in range(0,len(x),96000):
    clip=x[at:at+96000]
    if len(clip)<24000:continue
    wave=clip*.04/max(float(np.sqrt(np.mean(clip**2))),1e-8)
    with torch.inference_mode():score=float(model(torch.tensor(wave)[None],16000).item())
    assert np.isfinite(score);clips.append(score);weights.append(len(clip))
   assert clips;cache[key]=float(np.average(clips,weights=weights));cachepath.write_text(json.dumps(cache,indent=2))
  records.append(dict(filename=row['filename'],kind=kind,predicted_naturalness=cache[key],path=str(path),sha256=digest));print('MOS',row['filename'],kind,cache[key],flush=True)
summary=[dict(kind=k,mean_predicted_naturalness=float(np.mean([r['predicted_naturalness'] for r in records if r['kind']==k]))) for k in sorted({r['kind'] for r in records})]
report=dict(records=records,summary=summary,seconds=time.monotonic()-begin,normalization='same mono16k RMS0.04, nonoverlap6sec with1.5sec minimum tail',utmos_not_used_in_training=True,chinese_domain_unvalidated=True,not_human_approval=True,recognizer_used_as_loss_not_independent=True)
(OUT/((args.candidate+'.json') if args.candidate else ('with_pilot.json' if args.include_pilot else 'baseline.json'))).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('DONE',json.dumps(summary),flush=True)
