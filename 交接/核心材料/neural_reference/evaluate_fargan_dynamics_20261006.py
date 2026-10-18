from pathlib import Path
import subprocess,json,os,argparse
parser=argparse.ArgumentParser();parser.add_argument('--candidate',choices=['fargan_v8_dynamics','fargan_context_v9'],default='fargan_v8_dynamics');args=parser.parse_args()
base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';name=args.candidate
for filename in ('screen_board_phonetic_pilot_20261005.py','evaluate_board_phonetic_naturalness_20261005.py'):
    path=base/filename;text=path.read_text(encoding='utf-8')
    if repr(name) not in text:
        token="'fargan_v8_pitch_smooth_source_voicing']" if "'fargan_v8_dynamics'" not in text else "'fargan_v8_dynamics']"
        assert text.count(token)==1
        path.write_text(text.replace(token,token[:-1]+','+repr(name)+']'),encoding='utf-8')
env=os.environ.copy();env['PYTHONIOENCODING']='utf-8';env['TEMP']=env['TMP']='D:/Tools_codex/temp'
subprocess.run([str(base/'cosyvoice_env/Scripts/python.exe'),str(base/'screen_board_phonetic_pilot_20261005.py'),'--outname',name,'--validation-only'],env=env,check=True)
subprocess.run([str(base/'rvc_env/Scripts/python.exe'),str(base/'evaluate_board_phonetic_naturalness_20261005.py'),'--candidate',name],env=env,check=True)
screen=json.loads((budget/name/'heldout_screening.json').read_text(encoding='utf-8'))
s=next(r for r in screen['summary'] if r['kind']=='student')
mos=json.loads((budget/'phonetic_naturalness'/(name+'.json')).read_text(encoding='utf-8'))
score=next(r['mean_predicted_naturalness'] for r in mos['summary'] if r['kind']==name)
result=dict(candidate=name,characters=s['characters'],hanzi_edits=s['edits'],target_cosine=s['mean_target_cosine'],
            naturalness_diagnostic=score,baseline_hanzi_edits=7,content_gate_passed=s['edits']<=7,
            quality_accepted=False,project_completed=False,board_live_deployed=False,
            development_evaluation_not_blind=True,asr_and_speaker_scores_not_human_acceptance=True)
(budget/name/'development_gate.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('DYNAMICS_GATE',json.dumps(result),flush=True)
