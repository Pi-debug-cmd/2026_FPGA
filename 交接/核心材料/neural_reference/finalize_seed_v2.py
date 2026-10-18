"""Freeze genuine V2 evidence and one comparison; scores are not acceptance."""
from pathlib import Path
import argparse,json,hashlib
from collections import defaultdict
from importlib.metadata import distributions
from math import gcd
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
BASE=Path(__file__).resolve().parent;OUT=Path('D:/总进度/目标人物分析/SeedVC完整V2对照')
REVIEW=Path('D:/总进度/目标人物分析/音色与自然度复查');PERSONAL=Path('D:/总进度/目标人物分析/SeedVC人物微调')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while b:=f.read(4*1024*1024):h.update(b)
 return h.hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--selected');args=parser.parse_args()
 items=read(OUT/'conversion_items.json');cross=read(OUT/'v2_cross_eval.json');content=read(OUT/'v2_content_eval.json')
 cs={r['path']:r for r in cross['files']};ct={r['path']:r for r in content['files']}
 baseline_items=[r for r in read(REVIEW/'seed_neural_items.json') if r['group']=='seed_personal300_cfg03']
 baseline_items += [r for r in read(PERSONAL/'personal_cfg0.3_steps30_items.json') if r['test_name'] in ['fleurs_test_row3_id1852','BAC009S0004W0121']]
 baseline_cross=read(REVIEW/'review_cross_eval.json')['files']+read(PERSONAL/'personal_cross_eval.json')['files']
 baseline_content=read(REVIEW/'review_content_eval.json')['files']+read(PERSONAL/'all_content_eval.json')['files']
 bc={r['path']:r for r in baseline_cross};bt={r['path']:r for r in baseline_content}
 rows=[];integrity=[]
 for r in items:
  assert sha(r['path'])==r['sha256'] and sha(r['source_path'])==r['source_sha256']
  x,sr=sf.read(r['path'],dtype='float32');assert np.isfinite(x).all() and np.sqrt(np.mean(x*x))>1e-6
  integrity.append(dict(path=r['path'],sha256=r['sha256'],seconds=len(x)/sr,peak=float(np.max(np.abs(x))),
   clipped_fraction=float(np.mean(np.abs(x)>=.999)),source_hash_verified=True))
  a=cs[r['path']];b=ct[r['path']]
  rows.append(dict(label=r['label'],group=r['group'],test_name=r['test_name'],path=r['path'],
   cosine=a['wespeaker_raw_cosine_to_centroid'],mos=a['utmos_predicted'],cer=b['asr_character_error_rate'],asr_text=b['asr_text'],
   raw_pitch=b.get('raw_rmvpe_pitch'),spectral_distance=b.get('same_text_spectral_distance'),seconds=r['output_seconds']))
 for r in baseline_items:
  a=bc[r['path']];b=bt[r['path']]
  rows.append(dict(label=r['label'],group='rejected_personal_v1_matched4',test_name=r['test_name'],path=r['path'],
   cosine=a['wespeaker_raw_cosine_to_centroid'],mos=a['utmos_predicted'],cer=b['asr_character_error_rate'],asr_text=b['asr_text']))
 groups=defaultdict(list)
 for r in rows:groups[r['group']].append(r)
 summary=[]
 for group,records in groups.items():
  summary.append(dict(group=group,count=len(records),mean_cosine=float(np.mean([r['cosine'] for r in records])),
   min_cosine=float(min(r['cosine'] for r in records)),mean_mos=float(np.mean([r['mos'] for r in records])),
   mean_cer=float(np.mean([r['cer'] for r in records])),
   same_text_two=dict(mean_cosine=float(np.mean([r['cosine'] for r in records if r['test_name'] in ['zm_010','zf_001']])),
    mean_mos=float(np.mean([r['mos'] for r in records if r['test_name'] in ['zm_010','zf_001']])),
    mean_cer=float(np.mean([r['cer'] for r in records if r['test_name'] in ['zm_010','zf_001']])))))
 save(OUT/'matched_summary.json',dict(groups=summary,files=rows));save(OUT/'audio_integrity.json',integrity)
 print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
 if not args.selected:return
 selected=next(r for r in items if r['label']==args.selected)
 assert selected['test_name']=='zm_010' and not selected['convert_style']
 old=next(r for r in baseline_items if r['test_name']=='zm_010')
 assert old['source_sha256']==selected['source_sha256']
 source_paths=[Path('D:/总进度/目标人物分析/素材同文本普通声转换对比/目标人物原声_试听.wav'),Path(old['path']),Path(selected['path'])]
 labels=['目标人物原声','上次未通过的转换','新版转换'];pieces=[];provenance=[]
 for n,(p,label) in enumerate(zip(source_paths,labels),1):
  x,sr=sf.read(p,dtype='float32');x=x.mean(axis=1) if x.ndim==2 else x
  x=resample_poly(x,24000//gcd(sr,24000),sr//gcd(sr,24000))[:144000];assert len(x)==144000
  x*=min(.04/float(np.sqrt(np.mean(x*x))),.95/float(np.max(np.abs(x))))
  x[:120]*=np.linspace(0,1,120);x[-120:]*=np.linspace(1,0,120)
  dest=OUT/f'{n}_{label}_6秒.wav';sf.write(dest,x,24000,subtype='PCM_16');pieces.append(x)
  provenance.append(dict(order=n,label=label,original=str(p),original_sha256=sha(p),preview=str(dest),preview_sha256=sha(dest),seconds=6))
 audition=OUT/'18秒对照_目标原声_旧版_新版.wav';gap=np.zeros(4800,dtype='float32')
 sf.write(audition,np.concatenate([pieces[0],gap,pieces[1],gap,pieces[2]]),24000,subtype='PCM_16')
 save(OUT/'audition_provenance.json',dict(path=str(audition),sha256=sha(audition),seconds=18.4,clips=provenance,
  ordinary_source=selected['source_path'],ordinary_source_sha256=selected['source_sha256'],selected=selected,
  target_original_is_conversion_input=False,text_rewritten=False,speed_or_pitch_changed=False,
  preview_processing='First6 seconds, mono/resample24k/RMS-match/5ms fades; not word-aligned because different speaking rates.'))
 selected_metrics=next(r for r in rows if r['label']==args.selected)
 previous=read(OUT/'decision.json') if (OUT/'decision.json').exists() else {}
 decision=dict(status='awaiting_one_comparative_audition',selected=selected,selected_metrics=selected_metrics,
  groups=summary,conversions=len(items),input_audio_files=4,neural_presets=2,real_recordings=2,
  genuine_v2=True,ar_path_tested=True,ar_path_selected=False,previous_personal_v1_rejected=True,
  selection_reason='Select unadapted V2 CFM, not personal checkpoints: male MOS3.910/CER.0169/medianF0~194.6 vs rejected V1 MOS3.463/CER.0678; identity cosine falls.929 to.733. This is a naturalness-versus-identity diagnostic audition, not evidence of overall improvement. Personal V2 checkpoints did not preserve naturalness/content and are not selected.',
  audition=str(audition),hearing_result=None,subjective_acceptance=False,arbitrary_live_speaker_acceptance=False,
  board_deployed=False,board_latency_measured=False,causal_streaming=False,audio_uploaded=False,active_jobs=0,
  limitations=['Raw cosine is not percent likeness. Predicted MOS is not a Chinese listener rating.',
   'FLEURS metadata identifies gender, not a unique speaker ID; cannot infer number of distinct test people.',
   'Track9 excluded from training but previously repeatedly diagnosed, not untouched final test.',
   'Generic same-text transcript is ASR-derived and not manually proofread.',
   'Full teacher contains552384849 parameters; CFM/AR core size alone omits semantic/vocoder components.',
   'Offline quality result is not Zynq deployment/causal realtime feasibility.'])
 if previous.get('human_feedback'):
  for key in ['status','hearing_result','subjective_acceptance','human_feedback']:decision[key]=previous[key]
 save(OUT/'decision.json',decision)
 training=read(OUT/'personal_training/training_run.json')
 table='\n'.join(f"|{r['group']}|{r['count']}|{r['mean_cosine']:.4f}|{r['mean_mos']:.3f}|{r['mean_cer']:.4f}|" for r in summary)
 report=f'''# 完整Seed V2与目标人物适配对照

日期：2026-10-03。旧个人Seed V1试听反馈为“没什么进步、比目标原声厚重、有点不自然”，明确未通过；任何自动分数都不能覆盖这次反馈。

本轮实际执行完整V2（CFM＋AR；不同于先前文件名带v2却使用V1的模型）。固定源码51383efd921027683c89e5348211d93ff12ac2a8；新权重来自官方HF固定提交并通过SHA256，清单见model_load_validation.json。全部实际学习参数核对后加载，CAMPPlus旧dense命名按官方方式映射；HuBERT单独核对完整HF加载，再按官方配置保留前18层。完整管线实际{552384849:,}参数，不能把CFM/AR核心数字当完整网络。

先对两种普通合成声、两条真实中文录音（AISHELL与FLEURS）测试V2仅音色/AR＋音色两条路径，并分别用Track6前8秒与Track5前15秒作固定目标参考。16次零样本转换显示更换参考并未解决身份差距；AR路径出现漏字/重复的机器转写迹象，不选作当前候选。ASR也可能自己识别错，不把每个CER都当转换实际错误。

随后用Track5—8总{training['split']['total_seconds']:.2f}秒目标声音、25个连续约4秒片段，按官方forward_cfm损失与AdamW优化器适配300步，保留100/300两个权重；Track9与所有普通输入未参与训练。冻结特征/人物网络保持eval并缓存输出，batch1/FP32，LR2e-5，梯度裁剪1000，官方指数调度。上游t.squeeze把batch1时间变标量的问题通过形状恢复修正，数值与损失公式不变；不修改原预训练权重。实际训练{training['wall_seconds']:.2f}秒，峰值显存{training['peak_cuda_bytes']/1024**3:.2f}GiB。实际参数变化记录和权重SHA在personal_training/training_run.json。

本轮共{len(items)}次完整转换，采用相同的4种输入作对照；只称4个音频输入，不声称4名不同真人。旧个人V1基线使用相同源音频，不混用不同输入集的平均分。

|组别|输入数|中文身份原始余弦均值↑|自然度预测均值↑|ASR CER均值↓|
|---|---:|---:|---:|---:|
{table}

原始余弦不是“百分之多少像”。自然度预测不能判断鼻音、气声和厚薄是否像，频谱距离也不是人物身份验收。所有完整音频的有限数值、非静音、哈希、原输入未变与削波检查通过；音频及内容诊断保留在本目录。AR改变长度已记录，不以剪掉内容的方式强行对齐。

本次选择：{args.selected}，未人物适配的V2仅音色路线；没有选择100/300步适配权重。普通男声输入上，新结果自然度预测3.910（旧版3.463），ASR CER0.0169（旧版0.0678），F0中位约194.6Hz；中文身份余弦反而从旧版0.929下降到0.733。它展示了自然度与身份的取舍，不是“新版整体更好”。有必要用一次新架构对照确认实际厚薄/自然度是否改善，及人物音色是否更差；不能靠分数把旧版拒绝翻转。

18.4秒试听为①目标原声6秒→②上次未通过结果6秒→③新结果6秒，中间各0.2秒。②③都由同一个普通男声输入转换，目标原声只作比较。文本未改写，未做变速、调音高或均衡器变薄；仅试听副本音量匹配、重采样和端点淡入淡出。不同语速导致前三段6秒末尾未逐词对齐。来源与SHA见audition_provenance.json。

新结果尚未人耳接受，任意人实时输入与7020验收均未完成。普通TTS只用于可重复质量对照，最终工程仍是麦克风语音直接转换，不要求识别文本再合成。SD/板卡未改，没有上传音频；本轮所有作业已结束。需要先通过人物音色与自然度，再继续因果小模型、PS/PL预算与真实麦克风测试。

当前任务：只听①与③，比较目标人物音色、厚重感和自然度；②用于辨别是否比上一版改善。
'''
 (OUT/'本轮对照与试听说明.md').write_text(report,encoding='utf-8')
 (OUT/'environment_freeze.txt').write_text('\n'.join(sorted(f'{d.metadata["Name"]}=={d.version}' for d in distributions()))+'\n',encoding='utf-8')
 entry=f'''### 最新阶段：完整V2对照及目标人物适配，待一次短对照试听

已记录旧人物V1“没什么进步、厚重、不自然”拒绝，不默认已完成。执行完整Seed V2（AR＋CFM），4种固定普通输入×两条路径×两种目标参考，共16次；AR有漏字/重复迹象，当前不选。采用官方CFM训练损失在Track5—8的99.14秒上适配300步，保留100/300权重，原声、原模型、SD未改；Track9不用于训练，但已反复诊断，不是 pristine final holdout。追加两个训练节点各4个输入共8次，共24次新转换，未注册源人物。

当前候选`{args.selected}`只是筛选结果，待人耳接受。唯一18.4秒试听`{audition}`：①目标原声→②旧版→③新版，各6秒。旧版与新版使用同一个普通男声和相同文本，不把目标素材当转换输入。最新指标和完整性见同目录decision.json、matched_summary.json、audio_integrity.json、model_load_validation.json、personal_training/training_run.json。自动余弦/MOS/CER不代替自然音色验收。普通TTS仅作测试，最终目标仍是任意说话人麦克风直接转换到固定人物、核心在7020。

本轮任务全部结束，无后台作业，当前用户动作仅短试听，无须板卡上电或补录。完整教师552384849参数，没有部署上板、因果流式或实测延迟验收。学习线不变，本条优先于下文历史进展。

'''
 handoff=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');txt=handoff.read_text(encoding='utf-8')
 marker='## 最新工程进展：2026-10-03（优先于下文原有阶段计划）\n\n'
 if entry.split('\n')[0] not in txt:handoff.write_text(txt.replace(marker,marker+entry,1),encoding='utf-8')
 status=BASE.parent/'PROJECT_STATUS.md';txt=status.read_text(encoding='utf-8')
 en=f'''## Latest: genuine Seed V2 controls + personal CFM pilot — 2026-10-03

Prior V1 explicitly rejected as thick/unnatural. Completed24 V2 conversions on4 matched inputs (2 generic presets +2 real recordings):16 zero-shot CFM/AR across2 target refs, then100/300-step target-only CFM checkpoints each4 inputs. AR content problems disqualify selection for this stage. Official V2 CFM loss/AdamW;99.14s Track5-8 only, Track9 excluded but repeatedly diagnostic. Full verified teacher552384849 parameters, not core-only count. New candidate `{args.selected}` awaits one18.4s original→old-rejected→new audition; both conversions use same ordinary source, not target original. Metrics/hashes/loading/training auditable under `{OUT}`. Prior rejection remains; no subjective/live/causal/7020 acceptance, no audio upload/SD changes. All jobs complete; user's only requested action is audition; no new microphone data/power-on required. This supersedes historical statuses below.

'''
 if en.split('\n')[0] not in txt:status.write_text(txt.replace('# Zynq-7020 Low-Latency Voice Conversion Project\n\n','# Zynq-7020 Low-Latency Voice Conversion Project\n\n'+en,1),encoding='utf-8')
 print('AUDITION '+str(audition),flush=True)
if __name__=='__main__':main()
