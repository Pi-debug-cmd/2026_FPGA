"""Preserve all rejections; one targeted diagnostic audition, no promotion."""
from pathlib import Path
from collections import defaultdict
from importlib.metadata import distributions
from math import gcd
import json,hashlib
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
BASE=Path(__file__).resolve().parent;OUT=Path('D:/总进度/目标人物分析/局部音色包络校正')
KNN=Path('D:/总进度/目标人物分析/kNN语音单位转换');V2=Path('D:/总进度/目标人物分析/SeedVC完整V2对照')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def summaries(cross,content,items):
 c={r['label']:r for r in cross['files']};a={r['label']:r for r in content['files']};g=defaultdict(list);rows=[]
 for r in items:
  x=c[r['label']];y=a[r['label']]
  entry=dict(label=r['label'],group=r['group'],test_name=r['test_name'],cosine=x['wespeaker_raw_cosine_to_centroid'],
   predicted_mos=x['utmos_predicted'],asr_cer=y['asr_character_error_rate'],asr_text=y['asr_text'],
   spectral_distance=y.get('same_text_spectral_distance'),raw_f0=y.get('raw_rmvpe_pitch'))
  rows.append(entry);g[r['group']].append(entry)
 group=[dict(group=k,count=len(v),mean_cosine=float(np.mean([r['cosine'] for r in v])),
  mean_predicted_mos=float(np.mean([r['predicted_mos'] for r in v])),mean_cer=float(np.mean([r['asr_cer'] for r in v]))) for k,v in g.items()]
 return group,rows
def main():
 assert read(V2/'decision.json')['hearing_result']=='rejected'
 kitems=read(KNN/'conversion_items.json')+read(KNN/'cascade_items.json')
 kg,kr=summaries(read(KNN/'knn_cross_eval.json'),read(KNN/'knn_content_eval.json'),kitems)
 save(KNN/'stage_decision.json',dict(status='screened_no_candidate_promoted',groups=kg,files=kr,
  no_subjective_acceptance=True,board_deployed=False,conversions=12,
  reason='Direct retrieval and both cascade orders fail to retain identity/naturalness/content together; no extra audition requested for these outputs.',
  source_revision='c616845c4e309e24d5927f15adbdf277a3d65358'))
 items=read(OUT/'conversion_items.json')+read(OUT/'smoothed_items.json')
 eg,er=summaries(read(OUT/'envelope_cross_eval.json'),read(OUT/'envelope_content_eval.json'),items)
 checks=[]
 for r in kitems+items:
  assert sha(r['path'])==r['sha256'] and sha(r['source_path'])==r['source_sha256']
  x,sr=sf.read(r['path']);assert np.isfinite(x).all() and np.sqrt(np.mean(x*x))>1e-6
  checks.append(dict(label=r['label'],path=r['path'],sha256=r['sha256'],seconds=len(x)/sr,
   clipped_fraction=float(np.mean(np.abs(x)>=.999)),source_verified=True))
 assert all(r['clipped_fraction']==0 for r in checks)
 assert len(items)==12 and len(kitems)==12
 repro=read(OUT/'baseline_reproductions.json');assert len(repro)==4 and all(r['max_sample_error']==0 for r in repro)
 selected=next(r for r in items if r['label']=='smoothed_envelope_0.2_zm_010')
 score=next(r for r in er if r['label']==selected['label'])
 prior=read(Path('D:/总进度/目标人物分析/音色与自然度复查/review_decision.json'))
 old_metrics=prior['selected_metrics']
 # Reuse the first two already-heard preview clips exactly, including their
 # volume matching and fades. Only the third six-second clip changes.
 p1=V2/'1_目标人物原声_6秒.wav';p2=V2/'2_上次未通过的转换_6秒.wav'
 x,sr=sf.read(selected['path'],dtype='float32');x=resample_poly(x,24000//gcd(sr,24000),sr//gcd(sr,24000))[:144000]
 assert len(x)==144000;x*=min(.04/float(np.sqrt(np.mean(x*x))),.95/float(np.max(np.abs(x))))
 x[:120]*=np.linspace(0,1,120);x[-120:]*=np.linspace(1,0,120)
 p3=OUT/'3_音色校正实验_6秒.wav';sf.write(p3,x,24000,subtype='PCM_16')
 clips=[];provenance=[]
 for n,label,p in [(1,'目标原声',p1),(2,'上一轮较好的②原版本',p2),(3,'基于②的音色校正实验',p3)]:
  audio,rate=sf.read(p,dtype='float32');assert rate==24000 and len(audio)==144000;clips.append(audio)
  provenance.append(dict(order=n,label=label,path=str(p),sha256=sha(p),seconds=6))
 audition=OUT/'18秒诊断_目标原声_保留版本_音色校正.wav';gap=np.zeros(4800,dtype='float32')
 sf.write(audition,np.concatenate([clips[0],gap,clips[1],gap,clips[2]]),24000,subtype='PCM_16')
 save(OUT/'audition_provenance.json',dict(path=str(audition),sha256=sha(audition),seconds=18.4,clips=provenance,
  first_two_previews_identical_to_previous_audition=True,selected=selected,
  target_original_is_conversion_input=False,same_ordinary_male_source_as_previous=True,
  text_rewritten=False,manual_pitch_or_speed_change=False,comparison_not_word_aligned=True))
 decision=dict(status='awaiting_targeted_diagnostic_audition',overall_improvement_demonstrated=False,
  human_v2_feedback='二更好，三没有改进，反而退步了',preferred_comparison_baseline='Personal V1 step300 CFG.3, still not accepted',
  rejected_v2_kept_rejected=True,selected=selected,selected_metrics=score,previous_same_input_metrics=old_metrics,
  groups=eg,knn_groups=kg,conversions_this_turn=37,target_roundtrip_diagnostics=5,extra_baseline_reproductions=4,
  hearing_result=None,subjective_acceptance=False,arbitrary_live_speaker_acceptance=False,
  board_deployed=False,causal_streaming=False,board_latency_measured=False,audio_uploaded=False,active_jobs=0,
  selection_purpose='Not a winner: same male input/baseline, bounded/smoothed timbre residual; listener needed to judge thickness and identity. Predicted naturalness declines on male, improves on generic female; no overall gain.',
  audition=str(audition),next_if_rejected='Discard this envelope method as well; keep original preferred baseline and investigate training/teacher data strategy, not automatic promotion.',
  limitations=['Predicted MOS and embedding scores do not override listener judgments.',
   'Only the residual EMA is causal; WavLM and CFM consume future/full-clip context.',
   'Target Track9 is comparison only, not in retrieval/conditioning/training; repeatedly diagnosed, not pristine final holdout.',
   'kNN assets have HTTPS official release + API sizes/local hashes; release metadata has no independent publisher digest.',
   'No actual board or arbitrary live-speaker acceptance.'])
 old_decision=read(OUT/'decision.json') if (OUT/'decision.json').exists() else {}
 if old_decision.get('human_feedback'):
  for key in ['status','hearing_result','subjective_acceptance','human_feedback']:decision[key]=old_decision[key]
 save(OUT/'decision.json',decision);save(OUT/'audio_integrity.json',checks)
 table='\n'.join(f"|{r['group']}|{r['count']}|{r['mean_cosine']:.4f}|{r['mean_predicted_mos']:.3f}|{r['mean_cer']:.4f}|" for r in kg+eg)
 report=f'''# ③退步后的排查与局部音色校正

日期2026-10-03。用户明确认为上一轮②更好、③退步。完整V2候选保持拒绝，个人V1第300步/CFG0.3保留为相对较好的比较基线，仍未达到目标人物音色。以下工作没有证明整体进步，不能改写用户听感。

## 完成的隔离与不同机制试验

1. 原V1基线复现及目标条件隔离：13条转换、5条只经过BigVGAN的目标重建。重建身份对原片段余弦约0.994—0.997，只是诊断，不能证明所有听觉特征不变，也不能当任意人转换成果。改参考/多段平均条件未一致改善，未要求用户逐条试听，见`D:/总进度/目标人物分析/V1音色来源排查/音色来源排查说明.md`。
2. [官方kNN-VC](https://github.com/bshall/knn-vc/tree/c616845c4e309e24d5927f15adbdf277a3d65358)：用目标Track5—8共99.14秒建立4953×1024维第6层语音特征库，固定k4/prematched HiFiGAN。四个相同普通输入测试直接检索及两个V1组合方向，12条转换。没有源人注册、文本识别再合成、补充目标9、变调或时间拉伸。均未兼顾人物音色/自然度/中文内容，不推广，详见相邻kNN目录stage_decision.json。
3. 保留原V1 CFM生成的频谱，不重建普通输入文本。检索目标单位的频谱，只取正交DCT系数1—16的局部包络残差，保留能量系数0及高阶细节；逐帧缩放限制残差幅度0.8。不是全频谱替换或全局静态均衡器。先测0.25/0.5两强度，各4输入；自然度预测下降，不宣称改进。随后对残差作40ms因果EMA平滑，采用0.2强度，4个输入。残差相邻帧差异RMS降为原来的约30%，这是平滑诊断，不是人物验收。

音色校正前的4个V1基线与保留版本逐采样完全一致，见baseline_reproductions.json。排查时发现不同浮点归一化计算顺序导致真人人声准备PCM差1个24bit量化单位，可能传递到FP16输出；最终直接复用原基线准备PCM并重新生成全部正式校正结果，四组误差均0。早期失败日志保留，最终结果使用此次完整性记录。原训练权重、原人物声音和SD均未修改。

本轮新增37条转换（13目标条件、12检索/组合、12包络校正），另有5目标还原诊断和4条额外基线复现。输入始终是两种普通合成声及两条真实中文录音，不称四名不同真人；FLEURS没有唯一说话人ID。

## 相同4种输入的诊断

|组别|输入数|中文身份原始余弦均值|自然度预测均值|ASR CER均值|
|---|---:|---:|---:|---:|
{table}

保留V1同4输入基线：余弦0.9162，自然度预测3.451，CER0.1004，见上一轮matched_summary.json。自动数值不代表“百分之多少像”，MOS不是中文听众评分，CER包含ASR自身错误，机器生成同文本尚未人工逐字核对。

目前只选择一个**诊断试听**：平滑0.2校正的普通男声案例，仍是与上一轮相同的输入。其余弦约{score['cosine']:.4f}（旧0.9285），自然度预测{score['predicted_mos']:.3f}（旧3.463，反而下降），CER{score['asr_cer']:.4f}（旧0.0678），同文本MFCC-DTW距离约{score['spectral_distance']['mean_mfcc1_20_euclidean']:.2f}（旧约46.88）。普通女声案例的自然度预测提高，但男声没有同样改善，所以不能选择性声称整体更好，也不把该方法推广到板卡。

这次需要人耳仅判断局部校正是否减少厚重感、是否更像目标，及是否损害自然度。文件`18秒诊断_目标原声_保留版本_音色校正.wav`：①原声6秒→②保留原版本6秒→③局部校正6秒，间隔0.2秒。前两段直接复用上次试听文件，确保基线没有换；普通男声输入、文本、原模型均一致，没有把目标原声当讲话输入。③只在试听副本做音量匹配、24k重采样和5ms端点淡入淡出；未变速或手动升降调，三段6秒末尾不逐词对齐。

## 工程边界

目标库仅Track5—8。kNN源码c616845c4e309e24d5927f15adbdf277a3d65358，全部学习参数严格加载；WavLM315453120、HiFiGAN16523393参数。只使用作者官方HTTPS发布资产，API字节数核对、本地SHA记录用于固定复现；GitHub旧发布未给作者独立摘要，不能写成“已与官方SHA核对”。修改版MIT附加条款与LICENSE保留。包络校正还需要原V1/BigVGAN与WavLM，未证明7020预算可行。

只有包络EMA本身不看未来，完整语音特征/CFM转换依旧使用整段/未来上下文，不能称板载实时。所有文件哈希、非静音、有限值、无削波和原输入完整性核对完成。本轮作业全部结束；原声保留、SD未更新、没有音频上传。学习线不变，当前不需要上电、接线或补录。

当前任务：判断③的厚重感是否减轻、是否更接近①，还是②仍更好；这是诊断，不是完成版。
'''
 (OUT/'本轮排查与诊断试听.md').write_text(report,encoding='utf-8')
 (OUT/'environment_freeze.txt').write_text('\n'.join(sorted(f'{d.metadata["Name"]}=={d.version}' for d in distributions()))+'\n',encoding='utf-8')
 entry=f'''### 最新：③退步已记录，保留②并完成音色来源排查

用户明确认为上一轮“二更好，三没有改进，反而退步了”。完整V2候选保持拒绝，个人V1第300步/CFG0.3保留为较好的比较基线，但仍未通过目标人物验收。先完成目标重建/人物条件隔离13转换+5重建；再做官方kNN固定目标库的直接及两个组合方向12转换；最后做局部低阶音色包络残差12转换。合计37新增转换，未证明整体进步，不用自动分数覆盖用户意见。各方法全量结果保留，没有让用户逐版试听。

当前唯一需要用户动作是一次18.4秒**诊断对照**：`{audition}`。①目标原声、②上一轮较好的原版本、③基于②的平滑0.2包络校正，各6秒，前两段逐字节复用以前的试听，男声输入/文本/模型不变。③不是成功候选，其男声自然度预测低于旧版，只有部分音色/内容诊断轻微变化；需人耳判断厚重感是否减轻、是否更像目标，还是②仍好。不能把女声上的预测改善泛化为任意人改进。

全部任务已结束，无后台工作、音频上传或板卡/SD修改。目标库仅Track5—8共99.14秒，Track9仍是已反复诊断的对照、未入训练/条件。完整模型仍非因果，40ms EMA只是局部滤波器，本机运行快不能证明7020低延迟。四组V1基线已逐采样复现误差0。学习线不变，用户无须补录或上电。若新校正也失败，保留原基线、丢弃校正，不按分数自称进步。详细记录`{OUT}/本轮排查与诊断试听.md`和decision.json。本条覆盖下文历史待试听/方法计划。

'''
 handoff=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');text=handoff.read_text(encoding='utf-8')
 marker='## 最新工程进展：2026-10-03（优先于下文原有阶段计划）\n\n'
 if entry.split('\n')[0] not in text:handoff.write_text(text.replace(marker,marker+entry,1),encoding='utf-8')
 p=BASE.parent/'PROJECT_STATUS.md';text=p.read_text(encoding='utf-8')
 entry=f'''## Latest: reject V2 regression; targeted timbre diagnosis only — 2026-10-03

User prefers previous clip2; clip3 explicitly regressed. Personal V1 step300/CFG.3 kept as preferred-but-unaccepted baseline, V2 rejected. Completed37 new conversions:13 V1 reference/mean-style controls;12 official kNN/direct+both cascade orders;12 phone-local low-cepstral envelope variants including40ms EMA.5 target-only vocoder reconstructions are diagnostic, never conversion evidence.4 final V1 baselines reproduced sample-exactly; preserve original prepared PCM to avoid float-operation/PCM24-LSB propagation. No overall improvement shown. Single18.4s diagnostic original→unchanged preferred baseline→smoothed.2 envelope case requested under `{OUT}`; same ordinary male source/text/model, first2 previews identical to previous audition. Predicted male naturalness drops, female improves; not overall acceptance. Need listener thickness/identity/naturalness feedback; all jobs complete, no hardware/SD/audio upload/new recording action. Whole pipeline noncausal; only EMA has no future access. No arbitrary/live/7020 acceptance. Full audit in decision.json and report. Overrides earlier statuses.

'''
 if entry.split('\n')[0] not in text:p.write_text(text.replace('# Zynq-7020 Low-Latency Voice Conversion Project\n\n','# Zynq-7020 Low-Latency Voice Conversion Project\n\n'+entry,1),encoding='utf-8')
 print(str(audition),flush=True)
if __name__=='__main__':main()
