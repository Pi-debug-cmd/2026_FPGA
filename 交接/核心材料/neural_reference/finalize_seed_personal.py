"""Summarize actual personal-teacher experiments without claiming human acceptance."""
from pathlib import Path
import hashlib
import json
import shutil
import numpy as np
import soundfile as sf

BASE=Path(__file__).resolve().parent
ANALYSIS=Path('D:/总进度/目标人物分析')
OUT=ANALYSIS/'SeedVC人物微调'
PREV=ANALYSIS/'SeedVC下一阶段'
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    cross=read(OUT/'personal_cross_eval.json')['files']
    content=read(OUT/'personal_content_eval.json')['files']+read(OUT/'cfg_content_eval.json')['files']
    old_cross=[r for r in read(PREV/'validation_cross_eval.json')['files'] if r.get('group') in ['seed_strong_t6_8s_steps30','seed_strong_t6_8s_steps30_validation']]
    old_content=[r for r in read(PREV/'reference_matrix_content_eval.json')['files']+read(PREV/'validation_content_eval.json')['files'] if r.get('group') in ['seed_strong_t6_8s_steps30','seed_strong_t6_8s_steps30_validation']]
    for r in old_cross+old_content:r['group']='unadapted_rejected_teacher'
    cross+=old_cross;content+=old_content
    by_path={str(Path(r['path']).resolve()):r for r in content}
    groups=['unadapted_rejected_teacher','seed_personal_100','seed_personal_300','seed_personal_300_cfg0.0_steps30','seed_personal_300_cfg0.3_steps30']
    summaries=[]
    for group in groups:
        rows=[r for r in cross if r.get('group')==group]
        quality=[by_path[str(Path(r['path']).resolve())] for r in rows]
        assert len(rows)==8 and len(quality)==8
        same=next(r for r in quality if r['test_name']=='same_text')
        same_score=next(r for r in rows if r['test_name']=='same_text')
        summaries.append(dict(group=group,inputs=8,
            mean_raw_cosine=float(np.mean([r['wespeaker_raw_cosine_to_centroid'] for r in rows])),
            minimum_raw_cosine=min(r['wespeaker_raw_cosine_to_centroid'] for r in rows),
            mean_utmos=float(np.mean([r['utmos_predicted'] for r in rows])),minimum_utmos=min(r['utmos_predicted'] for r in rows),
            mean_asr_cer=float(np.mean([r['asr_character_error_rate'] for r in quality])),maximum_asr_cer=max(r['asr_character_error_rate'] for r in quality),
            same_text_mfcc_dtw=same['same_text_spectral_distance']['mean_mfcc1_20_euclidean'],
            same_text_utmos=same_score['utmos_predicted'],same_text_asr_cer=same['asr_character_error_rate']))
    items=read(OUT/'all_personal_items.json')
    checks=[]
    for r in items:
        assert sha(r['path'])==r['sha256'] and sha(r['source_path'])==r['source_sha256']
        x,sr=sf.read(r['path']);y,ysr=sf.read(r['source_path'])
        delta=abs(len(x)/sr-len(y)/ysr)
        assert np.isfinite(x).all() and np.sqrt(np.mean(x*x))>1e-6 and delta<.1
        checks.append(dict(label=r['label'],sha256=r['sha256'],duration_error_seconds=delta,
            clipped_fraction=float(np.mean(np.abs(x)>=.9999)),peak=float(np.max(np.abs(x))),rms=float(np.sqrt(np.mean(x*x)))))
    training=read(OUT/'training_run.json');split=read(OUT/'training_split.json')
    for r in split['train_originals']+split['train_segments']:
        assert sha(r['path'])==r['sha256']
    assert sha(split['heldout']['path'])==split['heldout']['sha256']
    for r in training['checkpoints']:assert sha(r['path'])==r['sha256']
    baseline=summaries[0]
    eligible=[r for r in summaries[1:] if r['mean_raw_cosine']>=baseline['mean_raw_cosine'] and
        r['minimum_raw_cosine']>=baseline['minimum_raw_cosine'] and r['mean_utmos']>=baseline['mean_utmos'] and
        r['minimum_utmos']>=baseline['minimum_utmos'] and r['same_text_utmos']>=baseline['same_text_utmos'] and
        r['mean_asr_cer']<=baseline['mean_asr_cer'] and r['same_text_mfcc_dtw']<=baseline['same_text_mfcc_dtw']]
    decision=dict(status='experiment_complete',training_completed=True,train_steps=300,new_conversions=len(items),
        checkpoint_candidates=training['checkpoints'],metrics=summaries,original_teacher_human_feedback='明显不像、有点不自然',
        original_teacher_human_acceptance=False,new_candidates_human_acceptance=None,
        automatically_joint_nonregressing_groups=[r['group'] for r in eligible],
        criterion='All8 average/min identity, average/min naturalness, same-text naturalness, mean CER and same-text spectral distance do not regress versus rejected baseline. Diagnostic screen only; NOT acceptance.',
        original_targets_unchanged=True,original_teacher_weights_preserved=True,
        source_speaker_enrollment=False,source_validation_used_for_training=False,audio_uploaded=False,
        causal_streaming=False,board_deployed=False,board_latency_measured=False,active_jobs=0,
        immediate_user_action='none; no further per-version audition or extra target recording requested',
        next_step='Address remaining timbre/naturalness gap; investigate semantic/prosodic leakage and target-reference consistency. Do not distill/deploy an unaccepted teacher; do not select solely by cosine.',
        limitations=['These are the same8 small diagnostic inputs; no claim of arbitrary-speaker acceptance.',
            'No listening result exists for the new fine-tuned files; the rejection refers to previous zero-shot candidate.',
            'Higher identity scores cannot establish perceptual thickness/nasality/breathiness.',
            'UTMOS/CER/MFCC diagnostics have known domain/content/prosody limitations.',
            'Generic SAPI source may contribute artificial prosody; this is an unproven confound, not an excuse for failure.',
            'Test inputs use PCM24 normalization instead of previous FLOAT; small precision difference is recorded.',
            '8s reference, fixed30steps, and one300-step training run do not establish architecture ceiling.'])
    save(OUT/'本轮决策.json',decision);save(OUT/'文件完整性.json',dict(status='complete',files=checks))
    save(OUT/'all_content_eval.json',dict(files=content,subjective_acceptance=False,board_deployed=False))
    names=['上一版通用参考（用户已否定）','个人微调100步 / CFG0.7','个人微调300步 / CFG0.7','个人微调300步 / CFG0','个人微调300步 / CFG0.3']
    table='\n'.join(f"| {name} | {r['mean_raw_cosine']:.4f} / {r['minimum_raw_cosine']:.4f} | {r['mean_utmos']:.3f} | {r['same_text_utmos']:.3f} | {r['mean_asr_cer']:.4f} | {r['same_text_mfcc_dtw']:.3f} |" for name,r in zip(names,summaries))
    screening=('存在未回退的诊断候选，但仍不构成听感验收。' if eligible else '没有一个版本同时满足本轮各项诊断不回退的筛选条件。因此不宣布新版本合格，也不要求用户再逐版试听。')
    report=f'''# 人物微调与不自然感排查：已完成的实验

日期：2026-10-03。**用户已明确否定上一版通用Seed教师：“还差一些，有点不自然；明显不像”。** 已记录验收失败。旧自动分数不能覆盖听感。本轮新微调文件没有用户试听结果，不能把它们称为已验收或已被用户否定。

## 实际动作

- 在独立目录用已有Track5～8共{split['total_seconds']:.2f}秒目标声音，完成Seed-VC V1较强模型的**300步个人微调**；原权重保留。25个连续片段，各约4秒，不丢句尾；Track9排除在训练之外，但它已用于多次诊断，不是未触碰的最终测试集。
- 按官方损失与AdamW更新转换网络和长度调整模块；固定随机种子20261003、batch1、FP32、LR1e-5。语义/人物参考/训练音色扰动网络冻结。训练损失不等于人物像不像。实际训练约{training['wall_seconds']:.1f}秒，峰值显存{training['peak_cuda_allocated_bytes']/2**30:.2f}GiB；均为电脑数据。
- 保存100/300步两个权重，分别转换原三个与新增五个输入。再在300步权重上对照CFG0和0.3，原设置为0.7。CFG控制条件预测的强化程度，不是“人物相似度百分比”，降低它未必更自然。
- 本轮共 **32个新转换**。输入人物均不注册、不加入训练；测试包含真实中文男女声，但FLEURS不提供人物ID，不能据两段女声声称两个不同女性。

## 固定八个输入上的诊断

| 版本 | 中文身份平均 / 最低 ↑ | 自然度预测平均 ↑ | 同文本合成输入自然度 ↑ | ASR CER平均 ↓ | 同文本MFCC-DTW ↓ |
|---|---:|---:|---:|---:|---:|
{table}

{screening}

分数只用于筛选：中文身份为WeSpeaker原始余弦，不是百分比；UTMOS不评价是不是目标人物，中文自然度可靠性未校准；MFCC-DTW也受语速、咬字、韵律影响；原声ASR本来就有错误。若声纹分提高而听起来不自然，不应继续只追分。300步在默认设置的身份均值/内容识别已有指标改善，整体自然度仍未明确改善，同文本自然度更低；不能宣称已修复用户反馈。

普通SAPI合成输入本身的韵律可能影响试听自然度，但目前没证据证明这就是失败原因。不能把问题推给用户或素材。现有约两分钟素材是否不足仍未证明，本轮不要求补录。

## 完整性、实现差异和可复现性

所有32输出SHA256、有限数值、非静音、时长差、削波均检查；削波文件数{sum(r['clipped_fraction']>0 for r in checks)}，最大时长差{max(r['duration_error_seconds'] for r in checks):.6f}秒。原始目标录音和原权重保持不变。两次保存权重均做有限值检查；另按整个状态字典比对，转换网络253个匹配浮点张量中234个变化，长度模块22个中20个变化（不是只看某个可能未使用的参数）。见weight_changes JSON。

官方训练构造器会加载一个在训练损失中完全未调用的冻结声码器，本轮只在训练阶段略去它，推理仍用同一BigVGAN。辅助网络显式eval/freeze；数据worker0；仅导出100/300步权重，不提供带优化器状态的续训检查点。这些差异、模型固定版本与SHA256均保存，没改官方损失。测试输入为单声道RMS0.04、PCM24，上一轮为FLOAT，量化差异很小但不是相同字节，已记录。

固定源码`51383efd921027683c89e5348211d93ff12ac2a8`；配置、资产版本/哈希、运行记录在training_run.json、training_split.json、inference_run.json、两份inference_cfg运行记录。新补充OpenVoice训练扰动模型和公开人物向量库，均从固定HF版本下载、SHA256验证；所有目标音频本机处理，没有上传。

## 当前结论和下一步

音色教师仍未通过用户验收，**不进入学生蒸馏或板卡部署**。原先通用教师被否定，人物微调还不足以证明已解决音色/自然度。下一阶段应排查内容编码中残留的源人物韵律/音色、目标参考一致性与生成细节，并用配对对照改进；不能无限增加轮数或按某一评分选模型。若引入其他教师架构，也要使用同一内容、源人物及参考，保持对比公平。

当前没有后台任务，板卡及SD均未改变，7020端到端延迟仍未测。整条电脑教师仍约3.10亿参数，个人微调没有把它变小或变成因果实时模型。用户暂时无需补录、接线、上电或逐版试听。

当前任务：继续解决教师的目标音色与自然度，再考虑7020小型实时模型。
'''
    (OUT/'人物微调与自然度排查说明.md').write_text(report,encoding='utf-8')
    entry=f'''### 用户否定后的个人微调与生成设置排查（已完成）

上一较强Seed/Track6零样本试听被用户明确否定“明显不像、有点不自然”，验收未通过。已用现有Track5～8共99.14秒完成独立300步Seed个人微调，保存100/300步权重，并在同一8输入对照默认CFG0.7及300步CFG0/0.3，共32段新转换；Track9不加入训练，源人物不注册、不参加训练。原模型与目标原声保留。

300步默认设置的中文身份均值0.9155（零样本0.8891）、ASR CER均值0.1496（0.1588）改善，但自然度平均3.4025（3.4103）未明确改善，同文本自然度3.238（3.572）下降。{screening}这些是诊断分数，新微调版本尚未试听，不是已通过或被用户否定；不能只凭声纹分继续推进。所有32文件完整性检查通过，无削波。全部训练/推理/评估任务已结束；无后台任务、音频上传、SD/板卡修改。学习线不变。

报告：`D:\\总进度\\目标人物分析\\SeedVC人物微调\\人物微调与自然度排查说明.md`，同目录`本轮决策.json`及逐文件记录。当前教师音色/自然度关口仍未通过，暂不蒸馏或部署。继续排查源人物信息残留、参考一致性和生成细节；不无条件增加轮次、不要求用户逐版听或立即补录。用户当前无上电/接线/录音任务。本条优先于下面更早的待评估/运行状态。

'''
    handoff=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md')
    s=handoff.read_text(encoding='utf-8');anchor='## 最新工程进展：2026-10-03（优先于下文原有阶段计划）\n\n'
    if entry.split('\n')[0] not in s:handoff.write_text(s.replace(anchor,anchor+entry,1),encoding='utf-8')
    status=BASE.parent/'PROJECT_STATUS.md';s=status.read_text(encoding='utf-8')
    entry_en=f'''## Latest: personal Seed adaptation after user rejection — 2026-10-03

- Prior zero-shot stronger candidate explicitly rejected as unlike target and somewhat unnatural; not accepted. Completed isolated official-loss personal training300steps on Track5-8,99.14s/25segments; Track9 excluded (reused diagnostic), no source enrollment/training on source validation. Saved100/300-step weights;4 conditions on same8 inputs (100/.7,300/.7,300/0,300/.3),32 outputs. All hashes/finite/non-silent/duration/clipping verified; originals and baseline preserved. Default300 mean Mandarin raw cosine0.9155 vs0.8891 and ASR CER0.1496 vs0.1588, but mean predictedMOS3.4025 vs3.4103 and same-text MOS3.238 vs3.572: no demonstrated naturalness repair. Joint non-regressing diagnostic groups: {decision['automatically_joint_nonregressing_groups']}. New versions have no human listening result; do not equate scores with acceptance.
- All current training/inference/evaluation jobs complete; none running. No audio upload, SD or board changes. Still full~310M offline noncausal teacher, no7020/live latency acceptance. Next diagnose target timbre/naturalness and source leakage/reference consistency before student work; no repeated per-version audition or mandatory fresh recordings. Report/decision: `D:\\总进度\\目标人物分析\\SeedVC人物微调`. Latest human rejection remains in force; new files are unassessed, not retroactively human-rejected.

'''
    if entry_en.split('\n')[0] not in s:status.write_text(s.replace('# Zynq-7020 Low-Latency Voice Conversion Project\n\n','# Zynq-7020 Low-Latency Voice Conversion Project\n\n'+entry_en,1),encoding='utf-8')
    print(json.dumps(dict(status='complete',outputs=len(items),metrics=summaries,joint_screen=decision['automatically_joint_nonregressing_groups'],report=str(OUT/'人物微调与自然度排查说明.md')),ensure_ascii=False))

if __name__=='__main__':main()
