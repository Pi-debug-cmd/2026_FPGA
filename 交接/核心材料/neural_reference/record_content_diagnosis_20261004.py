from pathlib import Path
import json
BASE=Path(__file__).resolve().parent
OUT=Path('D:/总进度/目标人物分析/内容保持模块隔离_2026-10-04')
NEXT=Path('D:/总进度/目标人物分析/中文文字到目标音色对照_2026-10-04')
def read(p):return json.loads(p.read_text(encoding='utf8'))
def main():
 experiment=read(OUT/'experiment_before_inference.json');pinyin=read(OUT/'free_pinyin_results.json');precision=read(OUT/'precision_pinyin_results.json');cross=read(OUT/'module_cross_eval.json')
 labels={r['label'] for r in read(OUT/'evaluation_items.json')};scores=[r for r in cross['files'] if r['label'] in labels]
 lines=['| 版本/输入 | 身份余弦（诊断） | 自然度预测（诊断） |','|---|---:|---:|']
 for r in scores:lines.append(f'| {r["label"]} | {r["wespeaker_raw_cosine_to_centroid"]:.4f} | {r["utmos_predicted"]:.3f} |')
 s=f'''# 内容保持模块隔离：结果与后续

2026-10-04。用户要求持续推进，直到确实需要协助或遇到问题。不再等待个人校准录音。

## 固定控制

固定同一目标Track6前8秒、输入、随机种子20261003、30步、CFG0.3，不加包络/均衡、不训练。内容适配器length_regulator和声学生成器CFM分别使用官方原权重或人物300步权重，完成2×2、3条真人输入。既有FLEURS基线解码采样最大误差0.0，确保比较控制。完整 learned weights 严格加载；补官方旧权重缺少的确定性timestep频率buffer，保留推理增长的positional cache，未替换或遗漏学习参数。官方文件中不使用的style_encoder/vq/f0权重不属于当前f0=false网络。

## 结果

FLEURS原声与只经过声码器的原声在两处篇章均被拼音工具解码为zhang；2×2的4个目标音色输出均为jiang。用源本人的录音作为诊断参考、只让模型保留源音色，也出现相同差异；该输出绝不能当目标人物转换成果。把冻结语音编码器从FP16改FP32，以及编码器和声学生成均用FP32，也未消除这两处差异。因而目前不支持靠简单回退微调或提高精度修好；不证明语义编码器单独就是根因，解码/特征瓶颈和检查器声音域偏差仍需区分。

另外两条发布方标注的真人句子用于额外检查：男声“别让我空着手回去”，女声“这就是答案”。源男声的拼音检查器自身把手写成shen，部分转换写成正确的shou，因此“与源识别不同”不能自动当作转换错误，优先同时核对发布方标签。模块互换没有稳定跨句收益，个别局部自然度预测也下降；不提供这4个弱变体的新试听、不切换默认模型、不宣布发音已修复。

## 交叉诊断分数

{chr(10).join(lines)}

这些分数不是听感验收或咬字通过率，特别是约2秒短句预测稳定性有限。发音审核保持未验证，已有用户“别”字失败保留。

## 后续路线

基于用户之前同意的文字中间路线，正在准备CosyVoice3官方对照：既检查其原生音频转换，也检查正确文字直接生成目标音色，最后保留真实ASR输出形成识别→目标生成对照。旧Whisper真实输入会把篇章写成偏张，不能偷偷使用正确文字再称端到端识别成功。参考人物与Track9排除训练/条件的约束不变，声音不上传。只有公开官方代码/权重下载；独立D盘环境保留旧环境不改。

CosyVoice3只作为电脑质量对照，未部署7020，不承诺150ms/板卡性能；官方流式输出能力不证明本机或本项目端到端低延迟。当前模型准备与试验在进行，最新结果将记录于 `{NEXT}`。需要有明确诊断意义的新成果时才请用户听一次。
'''
 (OUT/'隔离结果与后续.md').write_text(s,encoding='utf8')
 d=dict(status='module_and_precision_controls_complete_no_candidate_promoted',baseline_exact_reproduction=True,
  full_context_zhang_jiang_warning_persists_all_conditions=True,microtuning_or_precision_not_demonstrated_fix=True,
  unique_root_cause_proven=False,human_bie_failure_preserved=True,automatic_phonetic_detector_validated=False,
  source_training_or_enrolment=False,board_deployed=False,next_phase=str(NEXT))
 (OUT/'decision.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
 note=f'''## 最新：内容模块/精度回退无稳定改善，正在验证另一种语音生成架构（2026-10-04）

用户授权持续推进，遇问题或需协助才停。已固定参考/输入/种子，2×2交换原始/微调内容适配器与声学生成器，3个真人输入；旧基线逐样本精确复现。现有两处章→jiang机器差异在所有条件、同身份诊断、编码器FP32和全FP32均保留。不能认定某单一模块根因，也不能用源ASR错误当转换错误；没有稳定收益，不给弱变体试听，不升级默认版本。正在D盘独立环境准备CosyVoice3原生VC与中文文字→目标音色对照，用户此前同意文字中间路线；真实Whisper把篇章写成偏张，正确台词控制与真正ASR链路必须分开。详见 `{OUT / '隔离结果与后续.md'}`。旧权重/音频/环境/板卡/SD保留，发音失败仍未解决、7020实时未验收，新阶段尚在运行。

'''
 handoff=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');text=handoff.read_text(encoding='utf8');first,rest=text.split('\n',1)
 if '## 最新：内容模块/精度回退无稳定改善' not in text:handoff.write_text(first+'\n\n'+note+rest.lstrip('\n'),encoding='utf8')
 print('CONTENT DIAGNOSIS RECORDED',flush=True)
if __name__=='__main__':main()
