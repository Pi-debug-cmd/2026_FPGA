"""Preserve exact human rejection; do not transfer it to unlistened hashes."""
from pathlib import Path
import json, hashlib
PROJECT=Path('D:/Tools_FPGA/workspace/voice_conversion_zynq7020')
OUT=Path('D:/总进度/目标人物分析/固定原台词_分开试听_2026-10-04')
registry=Path('D:/总进度/目标人物分析/发音审核修正_2026-10-04/pronunciation_reviews.json')
manifest=json.loads((OUT/'decision.json').read_text(encoding='utf8'))
candidate=next(r for r in manifest['clips'] if r['order']==3)
assert hashlib.sha256(Path(candidate['path']).read_bytes()).hexdigest()==candidate['sha256']
feedback='不不不，三完全不行，变糊跟拖字还是比较明显的'
record=dict(audio_path=candidate['path'],audio_sha256=candidate['sha256'],result='failed',date='2026-10-04',
            reviewer='human user',feedback=feedback,listening_scope='Exact independent clip3, complete4.08004s same-text timing-only diagnostic.',
            issue='明显变糊、拖字；用户完全拒绝此候选',error_reproduced_by_validated_phone_model=False)
reviews=json.loads(registry.read_text(encoding='utf8'))
if not any(r['audio_sha256']==candidate['sha256'] and r['feedback']==feedback for r in reviews['reviews']):reviews['reviews'].append(record)
registry.write_text(json.dumps(reviews,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'human_feedback_rejected_timing.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
manifest['status']='timing_candidate_rejected_keep_original_synthesis';manifest['human_feedback']=record
candidate['human_acceptance']=False;candidate['human_rejected']=True;candidate['approved_for_training']=False
manifest['waveform_timing_warp_route_abandoned']=True;manifest['accepted_clip2_unchanged']=True
manifest['next_action']='Audit phase-free training-loss alignment; no interpolation-speed sweep, no audition pending.'
(OUT/'decision.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
pilot=Path('D:/总进度/目标人物分析/小模型监督对齐试验_2026-10-04/decision.json')
d=json.loads(pilot.read_text(encoding='utf8'));d['status']='waveform_warp_route_abandoned_after_same_text_human_rejection'
d['training_pairs_approved']=False;d['pending_user_audition']=False
d['human_rejection_provenance']=str(OUT/'human_feedback_rejected_timing.json')
d['unlistened_public_waveforms_not_individually_marked_human_failed']=True
pilot.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
from pronunciation_review_gate import assess,load_reviews
gate=assess(candidate,load_reviews());assert gate['status']=='failed_human_review' and not gate['can_auto_approve']
(OUT/'rejection_gate_check.json').write_text(json.dumps(gate,ensure_ascii=False,indent=2),encoding='utf8')
print('EXACT HUMAN FAILURE RECORDED; baseline preserved; warped training pairs blocked',flush=True)
