from pathlib import Path
import json,re
OUT=Path('D:/总进度/目标人物分析/独立中文发音检查验证_2026-10-04')
BASE=Path(__file__).resolve().parent
CALIB=Path('D:/总进度/发音审核校准')
REGISTRY=Path('D:/总进度/目标人物分析/发音审核修正_2026-10-04')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 CALIB.mkdir(exist_ok=True)
 text='是，是；戏，戏。\n这，这；借，借。\n别，别；鼻，鼻。\n别，别；蝶，蝶。\n这并不是告别。这是一个篇章的结束。'
 (CALIB/'校准录音台词.txt').write_text('发音检查工具校准，不是目标人物采集或输入者注册。\n\n请在安静环境中用正常声音读下面内容，各组之间停约半秒，最后一句正常连读。不要加音乐或变声，不要刻意把字读错。\n\n'+text+'\n\n录音约20—30秒，用手机录音即可；保存原文件到这个文件夹，WAV、M4A或MP3都可，不必为了格式重录。录后通知助手文件名。请自己确认各组是/戏、这/借、别/鼻、别/蝶确实读出了不同发音；如果某组口误，告知编号，不将其强行标为正确。\n\n用途：在不训练、不注册任何输入者的情况下，测试冻结的检查器是否能区分声母/韵母。人声转换目标仍是任意新讲话者转换为同一个目标人物；这份样本不是系统每换一个人都要采集的资料。\n',encoding='utf-8')
 synth=read(OUT/'sensevoice_synthetic_results.json')
 exploratory=read(OUT/'sensevoice_real_exploratory.json')['files']
 source=next(r for r in exploratory if r['label']=='actual_male_source')
 changed=[]
 for r in exploratory:
  if len(r['decoded'])!=len(source['decoded']):continue
  diffs=[dict(index=i,source_token=a,converted_token=b) for i,(a,b) in enumerate(zip(source['decoded'],r['decoded'])) if a!=b]
  changed.append(dict(label=r['label'],differences=diffs,
   inference='Unconstrained acoustic pinyin disagreement, suspected issue only; not human-confirmed phone diagnosis.'))
 save(OUT/'free_pinyin_disagreements.json',dict(source=source['label'],files=changed,
  full_speech_bie_still_identical=True,full_speech_detector_missed_known_bie_problem=True,
  suspected_zhang_to_jiang_not_gold_label=True))
 local=read(OUT/'fixed_local_probe.json')
 issues=[]
 for r in local['files']:
  if r['word']!='bie':continue
  actual=[re.sub(r'\d','',x) for x in r['recognized']['decoded']]
  issues.append(dict(label=r['source_label'],parent_path=r['parent_path'],parent_sha256=r['parent_sha256'],
   start_seconds=r['start_seconds'],end_seconds=r['end_seconds'],
   decoded=r['recognized']['decoded'],expected_body='bie',
   local_token_disagrees=actual!=['bie'],
   closed_hypothesis_best=r['counter_hypotheses'][0],
   warning_only=True,not_gold_phone_boundaries=True,not_validated_false_positive_rate=True))
 save(OUT/'local_bie_warning.json',dict(files=issues,automatic_approval=False,
  desired_use='Flag suspect localized speech while preserving human failures. No automatic success or exact error-label claim.'))
 decision=dict(date='2026-10-04',status='screening_complete_local_checker_provisional_needs_real_labelled_calibration',
  tested_recognizers=['Allosaurus uni2005 cmn frozen','SenseVoice dual pinyin CTC FP32 frozen'],
  synthetic_control_count=synth['count'],synthetic_intended_body_matches=synth['correct_intended_bodies'],
  synthetic_rate_is_not_validated_accuracy=True,synthetic_labels_not_human_gold=True,
  allosaurus_adopted=False,
  pinyin_checker_role='Exploratory local warnings only',
  full_speech_pinyin_missed_known_bie_error=True,
  local_source_and_roundtrip_decode='bie2',local_conversion_decode='ping2',
  known_human_failure_flagged_in_local_current_output=True,
  local_crop_boundaries_not_human_verified=True,independent_real_positive_negative_validation=False,
  actual_phone_substitution_proven=False,checker_cannot_auto_approve=True,
  suspected_full_speech_issue='Two source zhang1 decoded jiang1 in raw and all postprocessed conversions; exploratory.',
  conversion_model_retrained=False,new_voice_conversions=0,source_speaker_registration=False,
  synthetic_controls_not_target_training=True,board_deployed=False,causal_streaming=False,
  user_action='One normal20-30s labelled recording from script in D:/总进度/发音审核校准, then verify frozen checker without retraining.',
  current_user_voice_not_required_for_final_other_speakers=True,active_jobs=0)
 save(OUT/'decision.json',decision)
 report='''# 独立中文发音检查：验证结果与未解决项

2026-10-04。验证了两种独立工具，不改变人物模型，不训练输入者，不运行新人物转换，没有上传用户声音。

## 方法与结果

1. Allosaurus uni2005（约1113万参数）按官方cmn音素表直接输出音素。固定默认先验、完整cmn表，不向模型提供应读文字。运行32个合成的同声调最小对照（是/戏、这/借、别/蝶、别/鼻/白，两种声音×两种速度）。多处预期不同声母却给相同或不合理的声母；未采用为正式审核。合成输入尚未经人耳独立标注，结果是工具/控制不一致的筛查，不能全归因于识别器或报告为真人准确率。

2. SenseVoiceSmall双头拼音CTC，FP32 ONNX。官方权重按发布LFS SHA核对；原版FunASR前端函数/class从固定源码加载，只去掉注册装饰器，使用官方会选用的torchaudio Kaldi后台。前端16k、80mel、7×6 LFR、560维CMVN，固定默认dither随机种子。直接贪心解码拼音，未把汉字转拼音代替听音、未输入应读文本，未加语言模型。32个单字合成控制中，完整音节体符合预期11/32；短单字会出现额外音节和漏判。这个数字不是工具在人类录音上的准确率，控制标签本身也待人耳核实；因此不能宣布审核已可靠。

3. 对现有真人整句独立检查：源和仅声码器重建均输出zhang1，四个转换条件的对应两处均输出jiang1。提示“篇章”两个章字可能有声母/韵母保留问题，发生于未校正转换阶段也可见，单靠后处理不能解决。此为新的可疑线索，尚未人耳确认，不证明具体音素真的如此。

4. 整句拼音CTC仍把“别”写成bie2，峰值后验仍接近1；因此高置信度也会漏掉用户指出的发音问题，绝不能报告为近100%发音正确。另固定局部截取2.91—3.40秒（依据近似CTC峰和原先音素诊断，非人耳标注的边界）后，源/仅声码器重建读为bie2，未校正和其他转换读为ping2。局部切掉上下文时开始检出与应读音节不一致，保留为疑似异常警告。受截取边界和小片段分布影响，不能断言真的变成ping、不能仅据此评价其他全部音节。zhe/shi固定窗口有相邻音节混入，所有局部边界仍需验证。

## 当前结论

已完成筛查，并有一个能在当前“别”字局部片段发出警告的试验工具；它尚不能接替人耳发音验收，未建立真人正负对照上的可靠性。两工具均不自动批准声音、未覆盖已有的人耳失败。继续停止均衡/音色强度小变体试听。下一步需要一次明确台词的真人校准录音，验证冻结检查器，不据此训练人物模型或注册输入者。

## 用户需要提供的最小协助

用手机在安静环境正常读20—30秒：

是，是；戏，戏。
这，这；借，借。
别，别；鼻，鼻。
别，别；蝶，蝶。
这并不是告别。这是一个篇章的结束。

各组间停约半秒，最后一句连读，不加变声或音乐。原文件放D:/总进度/发音审核校准，可WAV/M4A/MP3，通知文件名即可。自己确认各组确实读出不同发音，口误告知；不把目标文字自动当音频的金标准。这份录音用于检查工具，不是项目要求每个新讲话者注册。源人的任意性目标与7020低延迟核心要求不变。

全部作业结束，暂无后台任务，SD/板卡和人物模型未改，人物转换质量仍未通过。原控制、权重、源码SHA和输出保留于本目录与D:/Tools_FPGA/workspace/voice_conversion_zynq7020/neural_reference下。

官方参考：https://github.com/xinjli/allosaurus ，https://huggingface.co/robinsonphan/sensevoice-small-zh-pinyin-dual-ctc ，https://github.com/modelscope/FunASR 。旧英文GOPT/IF-MDD不能直接视为中文审核器；G2PA缺少开箱即用的已验证审核权重，未为本任务直接采用。
'''
 (OUT/'验证结果与校准步骤.md').write_text(report,encoding='utf-8')
 policy_path=Path('D:/总进度/目标人物分析/真实输入与评价复核_2026-10-04/evaluation_policy.json')
 policy=read(policy_path)
 policy.update(automatic_phonetic_detector_validated=False,
  independent_phone_screening_report=str(OUT/'验证结果与校准步骤.md'),
  provisional_local_pinyin_warning_available=True,
  context_free_crop_not_final_validation=True,
  pinyin_high_posterior_not_pronunciation_correctness=True,
  next_input_control='Await one20-30s explicitly labelled real recording to validate frozen phone checker; no source enrollment/training.')
 save(policy_path,policy)
 for p,heading,body in [
  (Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md'),
   '## 最新：独立辨音筛查完成，局部别字能报警，仍需真人校准（2026-10-04）',
   '已验证Allosaurus与SenseVoice拼音CTC，固定官方权重与前端，未训练或改变人物转换。32合成同声调对照是预期标签，尚非人耳金标准；拼音工具完整音节体仅11/32匹配，不能称真人准确率，Allosaurus未采用。新整句工具发现源zhang→转换jiang两处可疑变化，但仍把人耳认为不清楚的别写为bie。固定局部别字窗口后源/原声重建为bie、转换为ping，可作为警告，局部边界/误报率仍未验证，不能宣布审核或声音修好。全局automatic_phonetic_detector_validated仍False，人耳失败保留。需用户一次20—30秒校准录音，台词在D:\总进度\发音审核校准\校准录音台词.txt；不训练/注册源人，不改变任意输入者目标。详见 '+str(OUT/'验证结果与校准步骤.md')+'。全部作业结束、无板卡/SD修改，仍未验收7020实时。'),
  (BASE.parent/'PROJECT_STATUS.md',
   '## Latest: independent phone screening, local bie warnings provisional — 2026-10-04',
   'Tested frozenAllosaurus/cmn and FP32SenseVoice dual pinyinCTC.32 intended synthetic controls, not human gold; full-body11/32 matches not real-speech accuracy. Allosaurus not adopted. Free whole-speechCTC suggests two zhang->jiang source/conversion differences, yet still confidently decodes known-bad bie. Fixed local crop2.91-3.40s gives source/vocoder-only bie2 and converted ping2; warning-only, unverified boundaries/false-positive rate. No automatic phonetic approval or speech repair. Await one20-30s human confirmed minimal-pair+connected-speech sample from D:\\总进度\\发音审核校准; no source training/enrollment. All jobs done, no new VC/board/SD change. Report '+str(OUT/'验证结果与校准步骤.md')+'.')]:
  s=p.read_text(encoding='utf-8')
  if heading not in s:
   first,rest=s.split('\n',1);p.write_text(first+'\n\n'+heading+'\n\n'+body+'\n\n'+rest,encoding='utf-8')
 print('SCREENING COMPLETE; REAL CALIBRATION NEEDED; NO CANDIDATE ACCEPTED',flush=True)
if __name__=='__main__':main()
