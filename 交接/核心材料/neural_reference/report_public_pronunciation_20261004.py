from pathlib import Path
import json,ast
BASE=Path(__file__).resolve().parent
OUT=Path('D:/总进度/目标人物分析/公开真人发音校准_2026-10-04')
VALID=Path('D:/总进度/目标人物分析/独立中文发音检查验证_2026-10-04')
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def main():
 manifest=read(OUT/'public_audio_manifest.json');checks=read(OUT/'public_checker_results.json')
 literal=read(OUT/'literal_word_samples.json');fixed=read(OUT/'fixed049_bie_sensitivity.json')
 allrows=manifest['files']+literal['files'];unique={r['path']:r for r in allrows}
 files=len(unique);speakers=len({r['speaker'] for r in allrows});seconds=sum(r['seconds'] for r in unique.values())
 totals={k:next(r for r in v if r['split']=='all' and r['syllable']=='all') for k,v in checks['summary'].items()}
 held={k:next(r for r in v if r['split']=='heldout_speaker' and r['syllable']=='all') for k,v in checks['summary'].items()}
 decision=dict(date='2026-10-04',status='public_natural_audio_collected_and_frozen_checker_screened',
  source='https://www.openslr.org/93/',repository_revision=manifest['policy']['revision'],license='Apache-2.0',
  labelled_target_tests=48,literal_word_examples=10,unique_original_wavs=files,known_speakers=speakers,total_original_seconds=seconds,
  new_user_recording_required=False,user_action='None required for this public-corpus calibration phase.',
  publisher_word_and_pinyin_labels_used=True,selection_before_inference=True,
  no_target_voice_training=True,no_source_speaker_enrolment=True,no_new_voice_conversion=True,
  results_all=totals,results_heldout_speaker=held,
  fixed049_bie_correct=fixed['correct_publisher_body'],fixed049_bie_count=fixed['n'],
  small_crop_false_alarms_demonstrated=True,old_ping2_is_not_proven_actual_substitution=True,
  full_sentence_ctc_still_misses_known_human_bie_failure=True,
  wrong_expected_label_controls_are_not_real_voice_conversion_error_gold=True,
  tones_not_scored=True,local_alignment_not_human_verified=True,
  automatic_phonetic_detector_validated=False,single_short_crop_can_reject=False,
  human_reported_conversion_failure_preserved=True,no_board_or_sd_changes=True,active_jobs=0,
  next_step='Use full context plus crop-length sensitivity only for provisional warnings; inspect content loss in uncorrected conversion using existing genuine inputs. Do not resume EQ sweep or claim phonetic repair.')
 save(OUT/'decision.json',decision)
 table=['| 检查方式 | 按发布方标签一致（48个目标位置） | 与标签不一致 | 未能判断 |',
 '|---|---:|---:|---:|']
 for field,label in [('full_target','整句自由拼音识别'),('local15','局部边界两侧各加0.15秒'),('local30','局部边界两侧各加0.30秒')]:
  r=totals[field];table.append(f'| {label} | {r["correct_label_count"]} | {r["false_alarm_on_publisher_label_count"]} | {r["abstained_count"]} |')
 report=f'''# 公开真人发音样本与审核校准结果

2026-10-04。用户建议网上采集，本阶段已完成；无需用户重新录制。以下取代上一阶段“等待20—30秒个人校准录音”的安排，该录音仅可选。

## 采集了什么

使用 [AISHELL-3官方说明](https://www.openslr.org/93/) 和 [AISHELL公开仓库](https://huggingface.co/datasets/AISHELL/AISHELL-3)。它是自然真人朗读，含发布方汉字、拼音标注及说话人资料，Apache-2.0。官方报告整体词与声调标注准确率超过98%；不能据此保证每条样本零错误。本次未逐个音素人工重新核验。

固定版本：`{manifest['policy']['revision']}`。48个预选目标位置覆盖shi4、xi4、zhe4、jie4、bie2、bi2、die2、bai2，每类6个（男女各3），并补10个含“是、戏、这、借、别”具体汉字的例句（男女各1）。合计{files}个不同原始WAV、{speakers}个有ID的真人、约{seconds:.1f}秒。部分原始句子检查两个不同目标，或被例句索引再次引用，不重复计为不同录音。原WAV不重编码，SHA256、文本、拼音、性别、ID、固定版本来源保存在清单中。

原始文件目录：`{BASE / 'public_pronunciation_calibration/audio'}`。具体例句入口：[真人例句索引](<{OUT / '真人例句索引.md'}>)。

## 如何检查

在看识别结果之前按发布方文字/拼音选样，冻结已下载的SenseVoice双头拼音CTC，不训练、不改权重或阈值。两位开发说话人与其余测试说话人分开，正式统计保留全部48个目标位置；补充10句不并入测试率。推理不输入正确文本、不限定可输出音节。整句后用序列对齐定位目标，声调暂不评分。局部使用发布方拼音的强制CTC对齐只估计截取时间，绝不把对齐当作发音正确证据；时间边界尚未人耳核验。个别拼音声调不在词表时，只为定位替换同音节体的固定词表声调，不能用于声调结论。

另外将自然真人音的“应读标签”故意改成相近音（shi/xi、zhe/jie、bie/bi等），检验基本音节区分能力。它不是实际模型误读、鼻音、音节边界变糊的金标准，不能以其通过率宣布转换审核已可靠。

## 冻结检查结果

{chr(10).join(table)}

未见过的说话人35个目标位置：整句34个与标签一致、1个不一致；0.30秒局部31个一致、3个不一致、1个未判断。故意错误标签在整句48个位置均未被接受，但这一简化任务不能代表实际转换发音错误检出率。

10个具体汉字补充例句的整句目标音节体均与标签一致。上述标签一致度受小样本、句子上下文、自动对齐和发布方标注错误影响，不是一般中文准确率，更不是当前转换音频的发音通过率。

专门将6条“别”真人录音切成与旧探针同长的0.49秒、按估计声学峰居中：只有{fixed['correct_publisher_body']}/6仍识别为bie，另外两条分别变为ji和bian；原整句这6处均为bie。说明短截取本身可制造异常，旧转换片段得到ping的结果只能保留为提示，不能证实真的念成ping，更不能因此确定根因。

## 对工程判断的影响

用户听到“别”不对的反馈仍然有效，当前人物转换未通过。新整句拼音工具也会漏掉该反馈；短片段工具还会误报。因此 `automatic_phonetic_detector_validated=false`，高分、汉字相同或单个短片段异常均不得自动批准或认定具体替换。已有zhang→jiang整句差异仍是待核实线索。保留所有失败反馈及旧模型，停止均衡/音色强度小变体试听。

后续用完整上下文和多种截取长度筛查，再依据现有真实输入定位未校正转换阶段的内容丢失。无需等待用户自己的录音；如需听感确认，应提供有明确诊断意义的少量片段。此次没有新增人物转换、训练、注册输入者或写SD/板卡；任意说话人到固定目标人物、7020低延迟核心目标不变。全部作业结束。
'''
 (OUT/'采集与校准结果.md').write_text(report,encoding='utf8')
 index=['# 真人例句索引','', '这些是网上公开的自然真人录音，文字和拼音来自AISHELL-3；用于校准审核工具，未做变声。每个“播放”链接打开原始WAV。','', '| 汉字 | 拼音 | 性别 | 原句 | 原始录音 |','|---|---|---|---|---|']
 for r in literal['files']:
  index.append(f'| {r["target_character"]} | {r["target_pinyin"]} | {"男" if r["gender"]=="male" else "女"} | {r["text"]} | [播放](<{r["path"]}>) |')
 index+=['',f'共{files}个不同原始WAV。完整48个测试位置、来源和校验信息见本目录public_audio_manifest.json、public_checker_results.json。','无需逐个试听或重新录制；当前尚不能宣称人物转换的发音问题已修好。']
 (OUT/'真人例句索引.md').write_text('\n'.join(index)+'\n',encoding='utf8')
 policy_path=Path('D:/总进度/目标人物分析/真实输入与评价复核_2026-10-04/evaluation_policy.json')
 policy=read(policy_path);policy.update(next_input_control='Public AISHELL-3 natural labelled audio calibration complete; no mandatory user recording. Full-context and crop-sensitivity screening only.',
  new_recording_required_to_continue=False,public_phone_calibration_report=str(OUT/'采集与校准结果.md'),
  public_labelled_phone_controls_completed=True,actual_converted_phone_error_gold_complete=False,
  automatic_phonetic_detector_validated=False,single_short_crop_can_reject=False)
 save(policy_path,policy)
 old=read(VALID/'decision.json');old.update(status='superseded_by_public_audio_calibration',user_action='None required; former own-recording request is optional and superseded.',
  public_calibration_decision=str(OUT/'decision.json'),public_labelled_audio_screened=True,
  local_crop_false_alarms_demonstrated=True,checker_cannot_auto_approve=True)
 save(VALID/'decision.json',old)
 oldreport=VALID/'验证结果与校准步骤.md';s=oldreport.read_text(encoding='utf8')
 s=s.replace('# 独立中文发音检查：验证结果与未解决项\n',f'# 独立中文发音检查：验证结果与未解决项\n\n> 最新安排：用户建议改用网上真人录音，已采集并完成公开语料筛查。以下要求个人录音的旧安排已取消，录音仅可选；短片段异常已发现误报，不能证明实际音节替换。最新结果见 [{OUT / "采集与校准结果.md"}](<{OUT / "采集与校准结果.md"}>)。\n',1)
 oldreport.write_text(s,encoding='utf8')
 note=f'''## 最新：公开真人发音资料已采集，个人录音不再必需（2026-10-04）

用户建议网上采集，已取AISHELL-3发布方汉字/拼音标注的真人录音：48个预选目标位置（8类各6）及10个含是/戏/这/借/别的具体例句，合计{files}个不同原WAV、{speakers}位真人，原音频/来源/固定版本/SHA已留存。冻结拼音工具整句46/48与音节体标签一致，未见说话人34/35；局部0.15秒边距仅28/48一致、0.30秒43/48且1未判断。6个别字固定0.49秒截取只4个仍读bie，证明截取会误报；旧ping探针不是具体音节替换证明。补充例句10/10仅标签一致，非实际错误检出率。新工具整句仍漏掉已有人耳别字问题，automatic_phonetic_detector_validated继续False、人耳失败保留，不得自动批准。无需用户录音/源注册；两条线目标不变。后续完整上下文+截取敏感性诊断，定位未校正转换的内容丢失，不继续EQ小变体。详见 `{OUT / '采集与校准结果.md'}`。全部作业结束，无新转换/训练/SD/板卡操作；7020实时未验收。

'''
 handoff=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');s=handoff.read_text(encoding='utf8');first,rest=s.split('\n',1);handoff.write_text(first+'\n\n'+note+rest.lstrip('\n'),encoding='utf8')
 project=BASE.parent/'PROJECT_STATUS.md';s=project.read_text(encoding='utf8');first,rest=s.split('\n',1)
 en=f'''## Latest: public natural-phone corpus collected; own recording optional — 2026-10-04

48 publisher-labelled AISHELL-3 target tests plus10 literal-word examples;{files} unique originalWAVs,{speakers} speakerIDs. Metadata, frozen revision andSHA saved. Frozen unconstrained pinyinCTC full-context46/48 body matches (heldout34/35), local margins0.15/0.30:28/43 matches with3/1 abstentions. Fixed0.49s genuine-bie crops only4/6 match versus6/6 whole context; short crops can create false warnings, prior ping result is not proven substitution. Wrong-expected-label controls are not real VC-error gold. No mandatory own recording/enrollment; human bie failure persists, automatic phone approvalFalse. Next full-context/crop-sensitivity diagnosis of uncorrected content loss, no EQ sweep. All jobs complete; no new VC/training/board/SD. Report `{OUT / '采集与校准结果.md'}`.

'''
 project.write_text(first+'\n\n'+en+rest.lstrip('\n'),encoding='utf8')
 for name in ['collect_public_pronunciation_20261004.py','validate_public_pronunciation_20261004.py','finish_public_pronunciation_20261004.py',Path(__file__).name]:ast.parse((BASE/name).read_text(encoding='utf8'))
 assert decision['automatic_phonetic_detector_validated'] is False and not policy['new_recording_required_to_continue']
 print(json.dumps(dict(unique_original_wavs=files,speaker_count=speakers,seconds=seconds,report=str(OUT/'采集与校准结果.md'),index=str(OUT/'真人例句索引.md'),status='complete'),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
