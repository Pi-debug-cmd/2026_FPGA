from pathlib import Path
import json,math,hashlib
import numpy as np
r=Path(__file__).resolve().parent
a=np.fromfile(r/'real_16000.small96_step9200.torch.f32',dtype='<f4');b=np.fromfile(r/'real_16000.small96_step9200.arm.f32',dtype='<f4')
assert len(a)==len(b)==16000 and np.isfinite(b).all()
err=float(np.sqrt(np.mean((a.astype('float64')-b)**2))/max(np.sqrt(np.mean(a.astype('float64')**2)),1e-12))
bench=json.loads((r/'bench_noise9200.json').read_text());assert err<1e-3 and bench['mean_chunk_ms']<13
old={x['case']:x for x in json.loads((r/'low_level_robustness.json').read_text())['cases']}
new={x['case']:x for x in json.loads((r/'noise9200_robustness.json').read_text())['cases']}
quiet_pass=new['zero']['steady_output_rms']<.0001 and all(new[k]['output_rms']<=new[k]['input_rms'] for k in ['noise_rms0.001','noise_rms0.002','noise_rms0.004'])
speech_retained=new['public_speech_rms0.04']['output_rms']>.01
assert quiet_pass and speech_retained
voice_ratio=new['public_speech_rms0.04']['output_rms']/old['public_speech_rms0.04']['output_rms']
screen=json.loads((r.parents[1]/'board_budget_20261005/small96_noise_refinement/heldout_screening.json').read_text(encoding='utf-8'))
edits=next(z['edits'] for z in screen['summary'] if z['kind']=='student')
report={'native_nrmse':err,'native_max_absolute_error':float(np.max(np.abs(a-b))),'actual_arm_benchmark':bench,
 'actual_arm_output_sha256':hashlib.sha256((r/'real_16000.small96_step9200.arm.f32').read_bytes()).hexdigest(),
 'bounded_noise_and_speech_level_checks_passed':quiet_pass and speech_retained,
 'synthetic_noise_output_reduction_db':20*math.log10(new['noise_rms0.001']['output_rms']/old['noise_rms0.001']['output_rms']),
 'steady_zero_output_reduction_db':20*math.log10(new['zero']['steady_output_rms']/old['zero']['steady_output_rms']),
 'public_normal_level_voice_change_db':20*math.log10(voice_ratio),
 'validation_student_character_edits':edits,'validation_previous_edits':22,'validation_characters':152,
 'content_regression':edits>22,'overall_quality_passed':False,
 'deployment_scope':'Temporary microphone noise/volume audition ONLY, content regression disclosed. Not final model acceptance.',
 'human_noise_acceptance_pending':True,'target_timbre_accepted':False,'board_acoustic_latency_measured':False}
(r/'noise9200_deployment_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
