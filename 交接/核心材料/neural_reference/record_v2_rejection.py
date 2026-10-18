from pathlib import Path
import json
BASE=Path(__file__).resolve().parent
OUT=Path('D:/总进度/目标人物分析/SeedVC完整V2对照')
p=OUT/'decision.json';d=json.loads(p.read_text(encoding='utf-8'))
d.update(status='human_rejected_regression',hearing_result='rejected',subjective_acceptance=False,
 human_feedback='二更好，三没有改进，反而退步了',pairwise_preferred='personal Seed V1 step300 CFG0.3 (clip2)',
 next_action='Retain clip2 as rejected-but-preferred comparison baseline; isolate V1 conditioning versus vocoder reconstruction.')
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
report=OUT/'本轮对照与试听说明.md';text=report.read_text(encoding='utf-8')
mark='## 最新反馈：③退步，②更好'
if mark not in text:
 report.write_text(text.replace('日期：',mark+'\n\n用户明确认为②更好、③没有改进反而退步。③完整V2候选未通过，停止当前V2候选推进；②也尚未达到目标音色，只作较好的比较基线。旧自然度预测提高与实际听感不一致，不再据此宣称改进。\n\n日期：',1),encoding='utf-8')
handoff=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');text=handoff.read_text(encoding='utf-8')
entry='''### 最新听感：完整V2退步，回到②排查

用户明确反馈“二更好，三没有改进，反而退步了”。完整V2候选拒绝；个人V1第300步/CFG0.3（②）保留为相对较好的比较基线，但仍有厚重/不自然问题，不能视为已通过。自动自然度预测与此次听感相反，后续不得据分数改写用户结论。

接下来分离检查：目标原声只经过频谱编码/声码器重建时是否失真；原V1同一权重与普通输入下，不同固定目标参考和多段平均人物条件的影响。重建目标原声只是定位故障，绝不能当任意人转换成果给用户试听。目标人物训练资料不增加，源人无需注册，板卡/SD不变。电脑排查完成且存在值得试听的结果，再请求一次对照。本文下文待V2试听等状态已过时。

'''
marker='## 最新工程进展：2026-10-03（优先于下文原有阶段计划）\n\n'
if entry.split('\n')[0] not in text:handoff.write_text(text.replace(marker,marker+entry,1),encoding='utf-8')
p=BASE.parent/'PROJECT_STATUS.md';text=p.read_text(encoding='utf-8')
entry='''## Latest human feedback: clip2 preferred; genuine V2 regressed — 2026-10-03

User rejects clip3 and prefers clip2. V2 candidate is not accepted. Personal V1 step300/CFG.3 remains only a rejected-but-preferred comparison baseline, not target acceptance. Predicted naturalness gain contradicted human judgment. Next isolate target-only vocoder reconstruction and fixed-reference/mean-style conditioning; target reconstruction is diagnostic, never any-to-one conversion evidence. No board/SD change, no source enrollment, no new recording requirement.

'''
if entry.split('\n')[0] not in text:p.write_text(text.replace('# Zynq-7020 Low-Latency Voice Conversion Project\n\n','# Zynq-7020 Low-Latency Voice Conversion Project\n\n'+entry,1),encoding='utf-8')
print('Human V2 rejection and preferred comparison baseline saved')
