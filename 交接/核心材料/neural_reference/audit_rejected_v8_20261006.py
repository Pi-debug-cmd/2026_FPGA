"""Offline diagnostics only. No new deployment or causal-root claim."""
from pathlib import Path
import json, numpy as np, datetime

base = Path(__file__).resolve().parent
budget = base.parent/'board_budget_20261005'
out = budget/'fargan_v8_rejection_audit'
out.mkdir(exist_ok=True)
manifest = json.loads((budget/'fargan_corpus_expanded/manifest.json').read_text(encoding='utf-8'))

def load(path):
    return np.fromfile(path,dtype='float32').reshape(-1,20).astype('float64')

def stats(f):
    active = f[:,0]>-7
    voiced = active & (f[:,19]>.1)
    adjacent = voiced[1:] & voiced[:-1]
    jumps = np.abs(np.diff(f[:,18]))[adjacent]*12
    return dict(frames=len(f),active_frames=int(active.sum()),voiced_frames=int(voiced.sum()),
                voiced_f0_median_hz=float(np.median(62.5*2**(f[voiced,18]+1.5))) if voiced.any() else None,
                adjacent_voiced_pairs=int(adjacent.sum()),
                pitch_step_semitone_mean=float(jumps.mean()) if len(jumps) else None,
                pitch_step_semitone_p95=float(np.quantile(jumps,.95)) if len(jumps) else None,
                pitch_steps_over_two_semitones=int((jumps>2).sum()),
                pitch_step_over_two_fraction=float((jumps>2).mean()) if len(jumps) else None,
                active_periodicity_mean=float(f[active,19].mean()) if active.any() else None)

rows=[]
for row in manifest['files']:
    if row['split']!='validation': continue
    stem=Path(row['filename']).stem
    source=load(row['source_features']);teacher=load(row['teacher_features'])
    predicted=load(budget/'fargan_mapper_expanded_v8'/(stem+'.converted.f32'))
    n=min(len(source),len(teacher),len(predicted));source,teacher,predicted=source[:n],teacher[:n],predicted[:n]
    active=source[:,0]>-7
    # Correlation of energy trajectories diagnoses paired temporal correspondence;
    # it cannot alone prove phoneme alignment or change training/runtime data.
    energy=[]
    for lag in range(-25,26):
        a=source[max(0,lag):min(n,n+lag),0]
        b=teacher[max(0,-lag):min(n,n-lag),0]
        energy.append((lag,float(np.corrcoef(a,b)[0,1])))
    best=max(energy,key=lambda r:r[1])
    rows.append(dict(filename=row['filename'],source=stats(source),teacher=stats(teacher),candidate=stats(predicted),
                     active_voicing_disagreement_source=float(np.mean((source[active,19]>.1)!=(predicted[active,19]>.1))) if active.any() else None,
                     active_voicing_disagreement_teacher=float(np.mean((teacher[active,19]>.1)!=(predicted[active,19]>.1))) if active.any() else None,
                     source_teacher_energy_correlation_lag0=dict(energy)[0],
                     best_energy_lag_frames=best[0],best_energy_correlation=best[1]))
targets=[dict(path=row['features'],stats=stats(load(row['features']))) for row in manifest['target_training']]
def aggregate(kind):
    valid=[r[kind] for r in rows if r[kind]['pitch_step_semitone_mean'] is not None]
    count=sum(s['adjacent_voiced_pairs'] for s in valid)
    return dict(adjacent_voiced_pairs=count,
                pitch_step_semitone_mean=sum(s['pitch_step_semitone_mean']*s['adjacent_voiced_pairs'] for s in valid)/max(count,1),
                pitch_steps_over_two_semitones=sum(s['pitch_steps_over_two_semitones'] for s in valid),
                pitch_step_over_two_fraction=sum(s['pitch_steps_over_two_semitones'] for s in valid)/max(count,1))
report=dict(updated=datetime.datetime.now().isoformat(),human_feedback='不像，而且声音不清晰，会颤',
            candidate_rejected=True,quality_accepted=False,project_completed=False,
            speaker_cosine_is_not_similarity_percentage=True,
            fixed_sentence_is_reused_development_example=True,
            human_feedback_overrides_machine_rank=True,
            baseline_hanzi_edits=7,candidate_hanzi_edits=15,total_characters=152,
            runtime_logs_before_rollback_empty=True,
            runtime_errors_not_required_for_audible_distortion=True,
            root_cause_confirmed=False,
            aggregate={k:aggregate(k) for k in ('source','teacher','candidate')},
            rows=rows,target_training=targets,
            next_gate='Do not audition solely on speaker cosine. Require no content regression on the frozen development set, pitch/voicing diagnostics, native throughput and explicit human acceptance; evaluate final generalization separately.',
            next_diagnostic='Use pitch/voicing ablations offline to test causal feature instability; do not deploy an unvalidated smoothing patch.')
(out/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ('candidate_rejected','aggregate','root_cause_confirmed')},ensure_ascii=False))
