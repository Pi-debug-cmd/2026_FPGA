"""Reject known regressions before any new human audition; not perceptual approval."""
from pathlib import Path
import json
r=Path(__file__).resolve().parent;budget=r.parents[1]/'board_budget_20261005'
weak=json.loads((budget/'weak_input_noise_aware/report.json').read_text(encoding='utf-8'))
screen=json.loads((budget/'small96_noise_aware/heldout_screening.json').read_text(encoding='utf-8'))
quiet=json.loads((r/'noise10400_robustness.json').read_text(encoding='utf-8'))
assert weak['complete'] and screen['complete']
w={(x['condition'],x['gain']):x for x in weak['summary']};q={x['case']:x for x in quiet['cases']}
cer=next(x for x in screen['summary'] if x['kind']=='student')
criteria={'normal_chinese_no_worse_than_6400':cer['edits']<=22,'weak_clean_no_worse_than_9200':w[('weak_clean',1)]['edits']<=7,'weak_noisy_chinese_improved':w[('weak_synthetic_colored_noise',1)]['edits']<=10,'colored_quiet_at_least_6db_lower_than_9200':w[('weak_synthetic_colored_noise',1)]['mean_quiet_rms']<=.001418152591213584/2,'zero_output_quiet':q['zero']['steady_output_rms']<.0001,'normal_public_speech_not_suppressed':q['public_speech_rms0.04']['output_rms']>.01}
report={'checks':criteria,'offline_rejection_screen_passed':all(criteria.values()),'validation_chinese':cer,'weak_gain1_clean':w[('weak_clean',1)],'weak_gain1_noise':w[('weak_synthetic_colored_noise',1)],'model_sha256':quiet['model_sha256'],'human_quality_accepted':False,'asr_not_pronunciation_approval':True,'target_timbre_accepted':False,'actual_mic_noise_not_evaluated':True,'board_candidate_not_deployed':True,'fixed_final_checkpoint_not_test_selected':True}
(budget/'small96_noise_aware/acceptance_screen.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
