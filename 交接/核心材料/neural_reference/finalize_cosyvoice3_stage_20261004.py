from pathlib import Path
import json,hashlib,ast
from math import gcd
from run_rvc_pilot import settings
settings()
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
BASE=Path(__file__).resolve().parent
OUT=Path('D:/总进度/目标人物分析/中文文字到目标音色对照_2026-10-04')
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 items=read(OUT/'cv3_evaluation_items.json');hanzi=read(OUT/'cv3_hanzi_evaluation_items.json')[0];phone=read(OUT/'cv3_free_pinyin_results.json');actualphone=read(OUT/'cv3_hanzi_free_pinyin.json')
 target=read(OUT/'target_same_text_pinyin.json');same=next(r for r in items if r['label']=='cv3_same_target_text')
 # Complete first sentence, including silence beyond chang; no half-second phone crop.
 emissions=target['emissions'];assert [r['pinyin'].rstrip('12345') for r in emissions[:19]]==['wo','de','xiao','yuan','hen','mei','zou','jin','da','men','jiu','neng','kan','jian','kuan','kuo','de','cao','chang']
 start=max(0,emissions[0]['approximate_peak_seconds']-.30)
 end=(emissions[18]['approximate_peak_seconds']+emissions[19]['approximate_peak_seconds'])/2
 specs=[dict(order=1,label='目标人物原声：我的校园很美…操场',path=target['path'],start=start,end=end,role='original target diagnostic; never conditioning or training'),
  dict(order=2,label='新引擎生成同一句中文：我的校园很美…操场',path=same['path'],start=0,end=None,role='Text-to-target synthesis, not live input proof'),
  dict(order=3,label='真实男声录音经实际识别再生成：这并不是告别…',path=hanzi['path'],start=0,end=None,role='Actual acoustic Hanzi output; prerecorded, not live or board deployment')]
 clips=[];provenance=[]
 for r in specs:
  x,sr=sf.read(r['path'],dtype='float32');x=x.mean(axis=1) if x.ndim==2 else x
  x=x[int(r['start']*sr):int(r['end']*sr) if r['end'] is not None else len(x)]
  if sr!=24000:x=resample_poly(x,24000//gcd(sr,24000),sr//gcd(sr,24000)).astype('float32')
  x*=min(.04/max(float(np.sqrt(np.mean(x*x))),1e-8),.95/max(float(np.max(np.abs(x))),1e-8))
  x[:120]*=np.linspace(0,1,120);x[-120:]*=np.linspace(1,0,120)
  p=OUT/f'试听{r["order"]}.wav';sf.write(p,x,24000,subtype='PCM_16');clips.append(x)
  provenance.append(dict(r,original_sha256=sha(r['path']),preview_path=str(p),preview_sha256=sha(p),seconds=len(x)/24000,
   no_pitch_shift_or_time_stretch=True,preview_rms_matched=True,original_preserved=True))
 combined=np.concatenate([clips[0],np.zeros(9600,dtype='float32'),clips[1],np.zeros(9600,dtype='float32'),clips[2]])
 audition=OUT/'新方案短对照_原目标声_同台词生成_真人识别生成.wav';sf.write(audition,combined,24000,subtype='PCM_16')
 assert np.isfinite(combined).all() and np.max(np.abs(combined))<.99
 save(OUT/'audition_provenance.json',dict(path=str(audition),sha256=sha(audition),seconds=len(combined)/24000,clips=provenance,
  purpose='One necessary human review: same-text target identity/naturalness, and whether zhe/shi/bie are clearly pronounced in actual ASR-to-target sample.',
  automatic_phonetic_acceptance=False))
 sourceasr=read(OUT/'sensevoice_hanzi_screening.json');source_rows=[r for r in sourceasr['files'] if r['role']=='genuine_source']
 cer_num=sum(r['character_edit_distance'] for r in sourceasr['files']);cer_den=sum(r['reference_character_count'] for r in sourceasr['files'])
 cross=read(OUT/'cv3_cross_eval.json');keep={r['label'] for r in items};scores=[r for r in cross['files'] if r['label'] in keep]
 decision=dict(date='2026-10-04',status='new_architecture_controls_complete_await_one_required_human_review',
  method='CosyVoice3 native VC and Chinese ASR->target synthesis; fixed reference, no personal retraining.',
  code_revision='074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc',model_revision='29e01c4e8d000f4bcd70751be16fa94bf3d85a18',
  fixed_target_reference='Track6 first8s; Track9 only reused diagnostic text/audio',
  whole_sentence_pinyin_warning_for_two_zhang_resolved_in_new_native_and_text_control=True,
  pinyin_checker_not_final_phonetic_validator=True,known_human_bie_failure_not_overridden=True,
  source_hanzi_asr_zero_character_ed_on_three_current_real_inputs=all(r['character_edit_distance']==0 for r in source_rows),
  hanzi_character_ed_on_public_and_current_real_inputs=cer_num,hanzi_reference_characters=cer_den,
  hanzi_observed_cer=cer_num/cer_den,asr_still_fallible=True,
  genuine_source_not_enrolled=True,target_voice_training=False,weights_sha_verified=True,
  half_storage='Qwen and flowFP16; HiFTFP32, strict complete pretrained weights.',
  native_new_male_zhe_zhuo_difference_not_ignored=True,
  text_generation_local_speed_not_realtime=True,board_deployed=False,causal_end_to_end_streaming=False,
  new_wavs_do_not_prove_any_speaker_realtime_on7020=True,candidate_promoted=False,subjective_acceptance=False,
  audition_path=str(audition),audition_sha256=sha(audition),audition_seconds=len(combined)/24000,
  required_user_help='Listen once: clip2 likeness/naturalness vs clip1; clip3 zhe/shi/bie articulation. No board or recording action needed.',
  active_jobs=0,next_if_quality_confirmed='Measure cached native-reference output streaming and first-audio latency; select teacher for small causal encoder/decoder and Zynq resource budget. Do not equate PC streaming with board deployment.')
 save(OUT/'decision.json',decision)
 table=['| 录音/方法 | 输出秒数 | 本机处理秒数 | 身份余弦（诊断） | 自然度预测（诊断） |','|---|---:|---:|---:|---:|']
 scoremap={r['label']:r for r in scores}
 for r in items:
  q=scoremap[r['label']];table.append(f'| {r["label"]} | {r["seconds"]:.2f} | {r["inference_seconds"]:.2f} | {q["wespeaker_raw_cosine_to_centroid"]:.4f} | {q["utmos_predicted"]:.3f} |')
 table.append(f'| 实际中文CTC识别→目标生成 | {hanzi["seconds"]:.2f} | {hanzi["inference_seconds"]:.2f}（生成部分） | 未另评分 | 未另评分 |')
 report=f'''# 新语音架构对照：待一次必要听感核对

2026-10-04。当前目标未完成，用户授权持续推进直到问题或确需协助。模块回退和精度对照没有稳定改善后，验证新架构；没有修改板卡或SD，没有上传录音。

## 本轮完成

采用 [CosyVoice官方仓库](https://github.com/QwenAudio/CosyVoice) 与 [官方CosyVoice3权重](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512)，固定源码/权重版本见decision.json。14个必要资产约4.44GB，发布方LFS SHA已核对；完整严格加载学习参数。Qwen从匹配config初始化，跳过重复BlankEN基础权重，完整llm.pt严格覆盖全部学习参数。首次内存不足后提前初始化CUDA，Qwen/flow改FP16存储，HiFT保留FP32；独立D盘环境不改变原RVC环境、旧教师/原录音。Matcha固定子模块dd9105b34bf2be2230f4aa1e4769fb586a3c824e。依赖兼容使用pyworld0.3.5、已有torch2.7.1，未用训练功能。无GPU ORT提供者，语音tokenizer实际CPU推理，未假称GPU加速。

固定原Track6前8秒参考，无追加人物训练、无输入说话人注册。比较3条真实输入的原生音频转换、正确文字控制、真实Whisper文字→目标生成、Track9已重复诊断的同文本生成。Track9声音/文本仅用于诊断对比，不进入参考或训练，不能称洁净最终测试。

新原生转换与正确文字生成在FLEURS整句拼音中保留两处zhang，之前四种权重组合与精度对照均为jiang，是跨架构的有用改善线索。工具本身会漏掉用户指出的“别”，因此这不是全面发音通过。新男声“空着手”仍有zhe/zhuo机器差异，不隐藏剩余问题。没有继续盲调CFG/训练/均衡。

## 真实文字识别与生成分开验证

旧Whisper把篇章写成偏张/偏僵。本轮解码已缓存SenseVoice双头ONNX的Hanzi输出，使用原SenseVoice版本一致的SentencePiece词表；直接声学贪心解码，只移除任务标签，未向识别器提供正确文字，未事后使用原文重写。3条当前真人输入字序列均与提供的文字一致。既有预选公共语料及当前输入共{cer_den}个汉字，出现{cer_num}个编辑差异（约{100*cer_num/cer_den:.2f}%）；小样本和发布方标签仍有限，非普遍ASR准确率。

直接用真实男声实际Hanzi结果（无手工补标点/文字）生成一个新音频，整句拼音与文字应读音节体吻合。这样正确文字控制和实际识别→生成链路都有记录，不把前者冒充端到端。尚非现场麦克风、任意未见输入者或上板验收。

## 性能与音质诊断

{chr(10).join(table)}

均为本机预录完整输入、非流式输出的耗时，不含现场输入积累，不代表端到端延迟。新原生转换的10.40秒音频用6.79秒，短句参考处理开销明显；文字生成仍慢于播放，不能宣称低延迟目标已达到，更不能套用官方150ms数字。后续需缓存固定人物条件、测流式首音时间，并压缩成7020能运行的因果学生模型；巨大电脑模型本身不是7020最终核心。

音色余弦与自然度预测不是听感验收：新原生FLEURS约0.8570/3.740，旧人物教师约0.9047/4.022；新架构内容有改善线索，但音色/自然度没有自动证实全面提升。新同目标台词生成约0.9008/3.926，准备一次同文本原声对比，交由人耳判断，不凭分数宣布成功。

## 必要的一次协助

试听总长{len(combined)/24000:.2f}秒：①目标人物原声的第一完整句；②新引擎生成相同文字；③已有真实男声录音经实际中文识别后生成（完整4.68秒，包含告别、篇章等）。前两段同文字，第三段用于检查这/是/别是否清晰；响度匹配，无变速变调、包络或均衡。原声完整句自动粗定位并保留上下文，不把截取后的ASR当验收证据。原音频保存。

请只反馈②像不像①、自然不自然；③这/是/别有无明显咬字问题。由于已证明检查器对“别”存在盲点，这一次听感是继续选择教师的必要信息。原人耳失败仍保留，新候选未自动批准。全部运行已结束，无需开板、更新SD或另录音。
'''
 (OUT/'本轮结果与必要协助.md').write_text(report,encoding='utf8')
 note=f'''## 最新：新架构出现内容改善线索，待一次必要短试听（2026-10-04）

内容模块/精度隔离无稳定收益后，完成CosyVoice3原生VC和文字→目标音色对照，固定Track6前8秒、无训练/源注册。官方14个资产约4.44GB已按LFS SHA核对，D盘独立环境，完整严格权重加载；Qwen/flow FP16，HiFTFP32。新原生和正确台词整句两处zhang保留，旧回退/高精度仍jiang；这只是改善线索，检查器对别仍有盲点，新男声另有zhe/zhuo差异。实际Hanzi声学识别3当前真人输入字序列正确，公共+当前529字16编辑差异；真实识别输出直接生成，没有偷偷用原文替代。新文字生成4.68秒音频耗12.19秒，未达到实时；新原生10.40秒耗6.79秒，也非现场因果延迟。原生音色/MOS诊断较旧弱，不能宣布全方面更好。{len(combined)/24000:.2f}秒一次必要试听：①目标原声完整首句②同台词新生成③真实男声经实际识别生成。需用户确认②像/自然否及③这是别的咬字，这是检查器无法代替的判断；未验收、未升级默认。详见 `{OUT / '本轮结果与必要协助.md'}`。作业均结束，无板卡/SD修改，任意输入者+7020低延迟目标仍未完成。

'''
 p=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');text=p.read_text(encoding='utf8');first,rest=text.split('\n',1)
 if '## 最新：新架构出现内容改善线索' not in text:p.write_text(first+'\n\n'+note+rest.lstrip('\n'),encoding='utf8')
 p=BASE.parent/'PROJECT_STATUS.md';text=p.read_text(encoding='utf8');first,rest=text.split('\n',1)
 en=f'''## Latest: new architecture controls ready; one necessary human review — 2026-10-04

CosyVoice3 nativeVC and text-target tests complete, fixedT6ref, no training/source enrollment.14 pinned assets4.44GB/LFS SHA verified; isolatedDenv, strict complete states, config-only Qwen init then strict llm.pt, Qwen/flowFP16 HiFTFP32. Two whole-context zhang retained versus jiang in all prior module/precision controls, provisional only; known human bie blind spot persists, new male zhe/zhuo issue retained. Acoustic Hanzi decode current3 real sources char-correct,16/529 edits across frozen public/current clips; actual ASR text directly synthesized. Native10.40s/6.79s PC processing, TTS4.68s/12.19s; no live-causal or7020 claim. Identity/MOS mixed/weaker, no automatic promotion. Need one{len(combined)/24000:.2f}s audition: target original complete first sentence, new same-text target synthesis, actual male ASR->target. Ask likeness/naturalness and zhe/shi/bie clarity. All jobs done, board/SD unchanged; overall goalactive, not complete. Report `{OUT / '本轮结果与必要协助.md'}`.

'''
 if '## Latest: new architecture controls ready' not in text:p.write_text(first+'\n\n'+en+rest.lstrip('\n'),encoding='utf8')
 policy_path=Path('D:/总进度/目标人物分析/真实输入与评价复核_2026-10-04/evaluation_policy.json');policy=read(policy_path)
 policy.update(next_input_control='Await one necessary human review of new architecture14s preview; no new source recording, board action, retraining or weak EQ variants.',
  new_recording_required_to_continue=False,new_architecture_decision=str(OUT/'decision.json'),automatic_phonetic_detector_validated=False)
 save(policy_path,policy)
 for name in ['run_cosyvoice3_controls_20261004.py','check_sensevoice_hanzi_20261004.py',Path(__file__).name]:ast.parse((BASE/name).read_text(encoding='utf8'))
 print(json.dumps(dict(audition=str(audition),seconds=len(combined)/24000,status='await_one_required_human_review',jobs=0),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
