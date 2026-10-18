from pathlib import Path
import datetime,json
base=Path(__file__).resolve().parent
native=base.parent/'board_support/native_llvc_20261005'
feedback=dict(date='2026-10-06',verbatim='杂音少了，咬字能接受',noise_reduced=True,intelligibility_acceptable=True,target_identity_accepted=False,project_complete=False,request='Continue autonomous improvement of target voice identity.')
for name in ['wide_live_trial_evidence.json','continued_refinement_evidence.json']:
 p=native/name;obj=json.loads(p.read_text(encoding='utf-8'));obj['human_feedback']=feedback;obj['human_new_model_feedback_pending']=False
 if 'wide_live_trial' in obj:obj['wide_live_trial']['human_feedback']=feedback;obj['wide_live_trial']['human_new_model_feedback_pending']=False
 obj['latest_board_observation']=dict(input_samples=602810224,chunks=2898126,mean_compute_ms=11.063855,max_compute_ms=26.888497,compute_deadlines_missed=15680,capture_pid=26793,convert_pid=26794,playback_pid=26795,playback_underruns_total=1,playback_underrun_ms=146.116,observation_note='Still running approximately10.47hours after start; original single underrun log unchanged.')
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
with Path('D:/总进度/原声验收后_模型改进_2026-10-05.md').open('a',encoding='utf-8') as f:
 f.write('\n\n## 2026-10-06用户反馈及继续方向\n\n用户明确反馈新版“杂音少了，咬字能接受”，授权继续改善目标声音。这个反馈验收了本候选现场清晰度和相对杂音改善，未验收最终目标音色。串口实际观察约10.47小时仍运行，均值11.063855ms/13ms块，原有一次146ms缓冲不足日志未新增。保留此候选为已试听基线，不再要求重复验收原声。下一阶段测试因果自动音高归一与神经音色模型联合处理；新增时域重叠拼接会增加缓冲和可能影响清晰度，必须先验证，再决定部署。不能把音高效果叫作完整目标音色转换。\n')
print('User feedback recorded; baseline retained.')
