"""Select a measured Pareto improvement or retain baseline; no subjective pass."""
from pathlib import Path
import json
import shutil
import numpy as np
import automatic_voice_evaluation as evaluation

OUT=evaluation.OUT

def main():
    report=json.loads((OUT/'candidates_评估记录.json').read_text(encoding='utf-8'))
    rows=[]
    groups=sorted({item['group'] for item in report['files']})
    for group in groups:
        files=[item for item in report['files'] if item['group']==group]
        if len(files)!=3: raise RuntimeError('Missing evaluation inputs')
        same=next(item for item in files if item['test_name']=='same_text')
        rows.append(dict(group=group,epoch=same['epoch'],index_rate=same['index_rate'],
            pitch_policy=same['pitch_policy'],model=same['model'],model_sha256=same['model_sha256'],
            same_text_mfcc_dtw=same['same_text_spectral_distance']['mean_mfcc1_20_euclidean'],
            same_text_asr_cer=same['asr_character_error_rate'],
            mean_asr_cer=float(np.mean([item['asr_character_error_rate'] for item in files])),
            mean_target_cosine=float(np.mean([item['target_centroid_cosine'] for item in files])),
            minimum_target_cosine=min(item['target_centroid_cosine'] for item in files),
            same_text_pitch=same['raw_rmvpe_pitch'],same_text_path=same['path'],
            signal_integrity_ok=all(item['nonfinite_samples']==0 and item['clipped_fraction']==0 for item in files)))
    baseline=next(row for row in rows if row['group']=='e60_index0.75_original')
    # Dominance is a relative screening rule, not an acceptance threshold.
    improving=[row for row in rows if row['signal_integrity_ok']
               and row['same_text_mfcc_dtw']<baseline['same_text_mfcc_dtw']
               and row['mean_asr_cer']<=baseline['mean_asr_cer']
               and row['minimum_target_cosine']>=baseline['minimum_target_cosine']]
    selected=min(improving,key=lambda row:row['same_text_mfcc_dtw']) if improving else baseline
    decision='relative multi-metric improvement candidate' if improving else 'retain baseline; no jointly improving candidate'
    current=dict(decision=decision,baseline=baseline,selected=selected,selection_rule=
        'Lower same-text MFCC-DTW distance, no higher mean ASR CER, no lower worst target cosine across 3 inputs, finite/unclipped audio.',
        user_acceptance=False,board_deployed=False,source_speaker_enrollment=False,
        causal_streaming=False,do_not_claim_human_likeness_percent=True,
        limitations=report['limitations']+['Selection on three inputs is not broad unseen-speaker acceptance.',
          'ASR and speaker models have known blind spots; user rejection of baseline remains authoritative.',
          'MFCC-DTW also includes articulation/prosody, and can favor metric fit over naturalness.'],
        all_groups=sorted(rows,key=lambda row:row['same_text_mfcc_dtw']))
    (OUT/'当前自动候选.json').write_text(json.dumps(current,ensure_ascii=False,indent=2),encoding='utf-8')
    # Stable audition copy is available if later desired; no repeated request to listen.
    shutil.copy2(selected['same_text_path'],OUT/'自动筛选候选_同文本约15秒.wav')
    lines=['# 自动评估与本轮改进结果','',
           '用户已明确认为60轮同文本结果与目标人物差距大；该反馈优先于任何自动分数。',
           '本轮无需新录音、无需逐版试听，板卡未更新；电脑本地训练到120轮。',
           '原60轮保留，在3个不同输入上比较17组设置、共51段转换。',
           '同文本输入是普通Kangkang合成声；另两种输入为未参与目标训练的AISHELL真实中文说话人。',
           '目标参考统计只使用Track5～8；Track9未进训练/检索，但反复用于诊断，不能当全新最终测试集。','',
           '## 自动评估能做什么、不能做什么','',
           '可以测相对声音向量、频谱特征距离、音高起伏、识别内容一致性及信号完整性。',
           '不能把余弦值解释为百分之多少像，也不能独立保证听起来就是目标人物或自然。',
           '原60轮同文本输出余弦0.9818，目标原声0.9846，用户却明确不满意，已证实该指标在本项目有盲区。',
           'Whisper在未转换的公开原声也出现错字，CER变化只作识别一致性代理，不能直接认定说话内容被改错。',
           'MFCC-DTW也包含韵律和吐字差异，不能作为人物相似度验收。','',
           '## 本轮筛选','',
           '筛选规则：同文本频谱距离下降，同时三种输入平均ASR错误率不升、最差说话人相似向量不降；音频完整、无数字削顶。',
           '决定：'+decision,'',
           '| 设置 | 同文本频谱距离↓ | 三输入平均ASR CER↓ | 三输入最小余弦↑ |',
           '|---|---:|---:|---:|']
    for row in current['all_groups']:
        lines.append(f"| {row['group']} | {row['same_text_mfcc_dtw']:.3f} | {row['mean_asr_cer']:.4f} | {row['minimum_target_cosine']:.4f} |")
    lines+=['','当前自动候选：`'+selected['group']+'`。这不是已通过听感验收或板上实时部署。',
             '候选试听文件只供之后需要时使用，不要求用户现在听。','',
             '## 音高条件试验与部署限制','',
             'target_range根据当前输入整段音高统计自动映射到目标参考中位数和变化范围，不需人物注册；这是离线试验，尚不因果。',
             'target_range_uv另保留RMVPE原始无声/无周期帧，试验辅音保护；当前上游默认会把零音高插值成正值。',
             '推理修改只在试验实例中绑定，不改原默认流水线；训练仍沿用原音高数据，因此UV试验还存在训练/推理条件差异。',
             '这些设置尚未部署到7020，最终仍须小型模型、因果处理、真实延迟与多人麦克风验证。','',
             '## 评估来源','',
             '- [Microsoft WavLM speaker verification model](https://huggingface.co/microsoft/wavlm-base-plus-sv)',
             '- [OpenAI Whisper-small model](https://huggingface.co/openai/whisper-small)',
             '- [RVC official source](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)',
             '', '本地模型修订、权重SHA256、完整识别文本和逐音频指标见JSON记录。']
    (OUT/'自动评估与改进说明.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(decision=decision,baseline=baseline,selected=selected),ensure_ascii=False),flush=True)

if __name__=='__main__': main()
