from pathlib import Path
import datetime,json,subprocess,sys

base=Path(__file__).resolve().parent
project=base.parent;native=project/'board_support/native_llvc_20261005';budget=project/'board_budget_20261005'
current=json.loads((native/'fargan_v8_live_evidence.json').read_text(encoding='utf-8'))
restored='native_llvc_wide192_shallow2_meter_arm ' in current['processes']['convert'].get('cmdline','')
assert restored and not current['v8_live_deployed']
feedback=dict(updated=datetime.datetime.now().isoformat(),verbatim='不像，而且声音不清晰，会颤',
              candidate='fargan_mapper_expanded_v8',candidate_rejected=True,quality_accepted=False,
              human_acceptance_pending=False,project_completed=False,baseline_restored_verified=restored,
              baseline='wide192_shallow2_target_anchor',baseline_target_identity_accepted=False,
              machine_score_does_not_mean_high_perceptual_similarity=True,
              runtime_snapshot='fargan_v8_rejected_trial_evidence.json',
              current_board_snapshot='fargan_v8_live_evidence.json')
(native/'v8_human_feedback.json').write_text(json.dumps(feedback,ensure_ascii=False,indent=2),encoding='utf-8')
prepared_path=native/'v8_trial_prepared.json';prepared=json.loads(prepared_path.read_text(encoding='utf-8'))
prepared.update(live_deployed=False,human_acceptance_pending=False,quality_accepted=False,
                candidate_rejected=True,baseline_restored_verified=True,human_feedback=feedback['verbatim'])
prepared_path.write_text(json.dumps(prepared,ensure_ascii=False,indent=2),encoding='utf-8')
decision_path=budget/'fargan_mapper_expanded_v8/decision.json'
decision=json.loads(decision_path.read_text(encoding='utf-8'))
decision.update(board_live_deployed=False,board_live_trial_performed=True,
                human_feedback=feedback['verbatim'],human_rejected=True,quality_accepted=False)
decision_path.write_text(json.dumps(decision,ensure_ascii=False,indent=2),encoding='utf-8')
rows=[]
for name in ('fargan_v8_pitch_smooth','fargan_v8_source_voicing','fargan_v8_pitch_smooth_source_voicing'):
    folder=budget/name;screen=json.loads((folder/'heldout_screening.json').read_text(encoding='utf-8'))
    summary=next(s for s in screen['summary'] if s['kind']=='student')
    mos=json.loads((budget/'phonetic_naturalness'/(name+'.json')).read_text(encoding='utf-8'))
    score=next(s['mean_predicted_naturalness'] for s in mos['summary'] if s['kind']==name)
    d=json.loads((folder/'decision.json').read_text(encoding='utf-8'))
    d.update(development_content_gate_passed=summary['edits']<=7,
             live_deployment_allowed=False,quality_accepted=False,
             rejection_reason='Content edits exceed accepted baseline 7/152; offline ablation does not establish naturalness/identity.')
    (folder/'decision.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    rows.append(dict(name=name,hanzi_edits=summary['edits'],characters=summary['characters'],
                     target_cosine=summary['mean_target_cosine'],naturalness_diagnostic=score,
                     content_gate_passed=d['development_content_gate_passed'],live_deployed=False))
audit_folder=budget/'fargan_v8_rejection_audit'
(audit_folder/'ablation_summary.json').write_text(json.dumps(dict(rows=rows,
    all_rejected_by_content_gate=all(not r['content_gate_passed'] for r in rows),
    target_similarity_not_accepted=True),ensure_ascii=False,indent=2),encoding='utf-8')
subprocess.run([sys.executable,str(base/'publish_oct6_refinement_20261006.py')],check=True)
doc=Path('D:/总进度/目标音色继续改进_2026-10-06.md')
with doc.open('a',encoding='utf-8') as f:
    f.write('\n## 否决后的固定三组离线消融结果\n\n```json\n'+json.dumps(rows,ensure_ascii=False,indent=2)+'\n```\n')
    f.write('\n三组均未达到旧基线7/152的内容检查门槛，全部保留离线，不请求用户再听，也不替换板上模型。仅提高余弦或平滑音高不足以解决字音/音色问题；继续方向是重新约束训练中的音高/相关性动态及内容保持。原数据源与教师能量轨迹相关0.927–0.972，最佳偏移0–1帧，未发现大幅整体错位；这不等于已证明逐音素对齐。已有actual_mic_diagnostic_20261005a输入只有恒定-1的PCM，不能拿它当真实讲话测试或训练素材。\n')
print(json.dumps(dict(baseline_restored=restored,candidate_rejected=True,ablations=rows),ensure_ascii=False))
