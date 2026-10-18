from pathlib import Path
import json,hashlib
from cosyvoice_pronunciation_frontend import prepare_text
P=Path('D:/总进度/目标人物分析/官方拼音发音控制对照_2026-10-04');Q=Path('D:/总进度/目标人物分析/中文文字到目标音色对照_2026-10-04')
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
plan=read(P/'experiment_before_inference.json');control=plan['cases'][0]
prepared=prepare_text(control['unmodified_actual_asr_text']);assert prepared['model_text']==control['phonetic_input']
contexts=[]
for text in ['告别','别人','别的','区别','别扭','别拗','不要告别，也别着急。','hello 123，你好。']:
 result=prepare_text(text)
 if text in ['别扭','别拗']:assert result['model_text']==text,result
 contexts.append(result)
save(P/'contextual_frontend_checks.json',dict(reproduces_user_improved_hint_input_exactly=True,cases=contexts,tests_only_text_policy_not_audio_pronunciation=True))
d=read(P/'decision.json');d.update(status='human_reports_bie_only_improvement_context_adapter_implemented',latest_human_feedback='对，后半段更好',bie_only_hint_retained=True,model_quality_acceptance_scope='Positive relative improvement on one exact listened sentence; clip2 likeness/naturalness baseline retained, not arbitrary-speaker or live-board acceptance.',required_user_help=None,active_jobs=0);save(P/'decision.json',d)
policy_path=Path('D:/总进度/目标人物分析/真实输入与评价复核_2026-10-04/evaluation_policy.json');policy=read(policy_path);policy['next_input_control']='Clip2 accepted for timbre/naturalness baseline; bie-only candidate relative improvement confirmed. Check context/multispeaker content and independent small causal hardware feasibility; no current listening request pending.';policy['latest_human_feedback']=['2就很好，3我感觉再改就得费很大劲了吧','对，后半段更好'];save(policy_path,policy)
rp=Path('D:/总进度/目标人物分析/发音审核修正_2026-10-04/pronunciation_reviews.json');registry=read(rp);audio=P/'原③与别字拼音控制_约10秒对照.wav';digest=hashlib.sha256(audio.read_bytes()).hexdigest()
if not any(r['audio_sha256']==digest for r in registry['reviews']):registry['reviews'].append(dict(audio_path=str(audio),audio_sha256=digest,result='partial',date='2026-10-04',reviewer='human user',feedback='对，后半段更好',listening_scope='Second whole-sentence segment of exact9.72s composite; user confirms relative improvement, not all phones or all inputs.',issue='bie-only hint improves perceived articulation; broad phonetic acceptance remains unproven.',error_reproduced_by_validated_phone_model=False))
save(rp,registry)
print('USER IMPROVEMENT RECORDED, CONTEXT POLICY INPUT EXACTLY REPRODUCES LISTENED CONTROL')
