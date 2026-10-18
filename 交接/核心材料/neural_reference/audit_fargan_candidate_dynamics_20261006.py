from pathlib import Path
import numpy as np,json,argparse
parser=argparse.ArgumentParser();parser.add_argument('--candidate',required=True);args=parser.parse_args()
assert args.candidate in ('fargan_v8_dynamics','fargan_context_v9')
base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';folder=budget/args.candidate
manifest=json.loads((budget/'fargan_corpus_expanded/manifest.json').read_text(encoding='utf-8'));rows=[]
for row in manifest['files']:
    if row['split']!='validation':continue
    stats={}
    paths=dict(source=row['source_features'],teacher=row['teacher_features'],candidate=folder/(Path(row['filename']).stem+'.converted.f32'))
    for kind,path in paths.items():
        f=np.fromfile(path,dtype='float32').reshape(-1,20)
        voiced=(f[:,0]>-7)&(f[:,19]>.1);pairs=voiced[1:]&voiced[:-1]
        jumps=np.abs(np.diff(f[:,18])[pairs])*12
        stats[kind]=dict(adjacent_pairs=len(jumps),mean_semitone_step=float(jumps.mean()),over_two_semitones=int((jumps>2).sum()),p95_semitone_step=float(np.quantile(jumps,.95)))
    rows.append(dict(filename=row['filename'],stats=stats))
aggregate={}
for kind in ('source','teacher','candidate'):
    count=sum(r['stats'][kind]['adjacent_pairs'] for r in rows)
    aggregate[kind]=dict(adjacent_pairs=count,mean_semitone_step=sum(r['stats'][kind]['mean_semitone_step']*r['stats'][kind]['adjacent_pairs'] for r in rows)/count,over_two_semitones=sum(r['stats'][kind]['over_two_semitones'] for r in rows))
report=dict(candidate=args.candidate,rows=rows,aggregate=aggregate,root_cause_confirmed=False,diagnostic_not_human_acceptance=True)
(folder/'pitch_dynamics_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(aggregate),flush=True)
