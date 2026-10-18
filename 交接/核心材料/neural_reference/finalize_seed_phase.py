"""Freeze completed PC reference/teacher tests and produce a short audition."""
from pathlib import Path
import hashlib
import json
import shutil
from collections import defaultdict
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from math import gcd

BASE = Path(__file__).resolve().parent
ANALYSIS = Path('D:/总进度/目标人物分析')
OUT = ANALYSIS / 'SeedVC下一阶段'

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def save(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    shutil.copy2(ANALYSIS/'中文交叉评估/中文交叉评估结果.json', OUT/'validation_cross_eval.json')
    shutil.copy2(ANALYSIS/'自动评估与改进/seed_new_input_validation_评估记录.json', OUT/'validation_content_eval.json')
    cross = read(OUT/'validation_cross_eval.json')
    content = read(OUT/'validation_content_eval.json')
    strong = read(OUT/'strong_run.json')
    fresh_strong = read(OUT/'strong_validation_run.json')
    items = read(OUT/'phase_items.json') + read(OUT/'rvc_validation_items.json') + read(OUT/'strong_validation_items.json')
    integrity = []
    for row in items:
        path = Path(row['path'])
        if sha(path) != row['sha256']:
            raise RuntimeError('Output changed: '+str(path))
        if row.get('source_sha256') and sha(row['source_path']) != row['source_sha256']:
            raise RuntimeError('Original input changed')
        audio, rate = sf.read(path, dtype='float32')
        source, source_rate = sf.read(row['source_path'], dtype='float32')
        duration_error = abs(len(audio)/rate - len(source)/source_rate)
        rms = float(np.sqrt(np.mean(audio.astype(np.float64)**2)))
        if not np.isfinite(audio).all() or rms < 1e-6 or duration_error > .1:
            raise RuntimeError('Output integrity failed')
        integrity.append(dict(label=row['label'], path=str(path), sha256=sha(path),
            seconds=len(audio)/rate, source_seconds=len(source)/source_rate,
            duration_error_seconds=duration_error, rms=rms,
            peak=float(np.max(np.abs(audio))),
            clipped_fraction=float(np.mean(np.abs(audio)>=.9999))))
    manifest = read(BASE/'public_chinese_validation/validation_manifest.json')
    for row in manifest['files']:
        if sha(row['path']) != row['sha256']:
            raise RuntimeError('Fresh original changed')
    # Float WAV headers include PEAK timestamps. Verify samples independently of headers.
    refs = read(OUT/'参考片段清单.json')
    pcm_records = {}
    pool = []
    for n in range(5, 9):
        row = refs[f't{n}_8s']
        x, sr = sf.read(row['original'], dtype='float32')
        if x.ndim == 2:
            x = x.mean(axis=1)
        clip = x[:sr*8]
        clip = clip*.04/max(float(np.sqrt(np.mean(clip*clip))), 1e-8)
        actual, rate = sf.read(row['path'], dtype='float32')
        if sha(row['original']) != row['original_sha256'] or rate != sr or not np.array_equal(actual, clip):
            raise RuntimeError('Reference waveform mismatch')
        pcm_records[f't{n}_8s'] = dict(path=row['path'], current_file_sha256=sha(row['path']),
            decoded_mono_f32le_sha256=hashlib.sha256(actual.astype('<f4').tobytes()).hexdigest(),
            sample_rate=rate, original_sha256=row['original_sha256'],
            formula='first 8 seconds, stereo mean, RMS .04, no resampling')
        pool.append(clip[:sr*6])
    pooled, sr = sf.read(refs['pool24s']['path'], dtype='float32')
    if not np.array_equal(pooled, np.concatenate(pool)):
        raise RuntimeError('Pooled reference mismatch')
    pcm_records['pool24s'] = dict(path=refs['pool24s']['path'], current_file_sha256=sha(refs['pool24s']['path']),
        decoded_mono_f32le_sha256=hashlib.sha256(pooled.astype('<f4').tobytes()).hexdigest(),sample_rate=sr,
        formula='concatenate first 6 seconds of each RMS-normalized 8-second reference, Track5/6/7/8')
    save(OUT/'reference_pcm_integrity.json', dict(status='complete',references=pcm_records,
        note='Reference files were regenerated between runs; historical byte hashes remain unchanged in run logs. Current decoded samples match the deterministic source formula exactly. FLOAT WAV PEAK header timestamps can change byte hashes without changing samples.'))
    groups = {row['group']: row for row in cross['groups']}
    cergroups = defaultdict(list)
    for row in content['files']:
        cergroups[row['group']].append(row['asr_character_error_rate'])
    selected_groups = ['rvc_e120_target_range_validation', 'seed_strong_t6_8s_steps30_validation', 'seed_strong_pool24s_steps30_validation']
    metrics = []
    for name in selected_groups:
        row = dict(groups[name])
        row.update(mean_asr_cer=float(np.mean(cergroups[name])),maximum_asr_cer=max(cergroups[name]))
        metrics.append(row)
    selected = next(row for row in strong['files'] if row['reference_name']=='t6_8s' and row['test_name']=='same_text')
    target_path = Path(selected['same_text_target'])
    output_path = Path(selected['path'])
    clips = []
    audition_sources = []
    for name, path in [('目标人物原声_10秒', target_path), ('新方案转换_10秒', output_path)]:
        x, rate = sf.read(path, dtype='float32')
        if x.ndim == 2:
            x = x.mean(axis=1)
        x = x[:rate*10]
        factor = gcd(rate, 24000)
        x = resample_poly(x,24000//factor,rate//factor).astype(np.float32)[:240000]
        x *= .04/max(float(np.sqrt(np.mean(x*x))), 1e-8)
        peak = float(np.max(np.abs(x)))
        if peak > .95:
            x *= .95/peak
        # Only 5 ms at the ends are faded to avoid clicks at the audition join.
        fade = 120
        x[:fade] *= np.linspace(0,1,fade,dtype=np.float32)
        x[-fade:] *= np.linspace(1,0,fade,dtype=np.float32)
        dest = OUT/(name+'.wav')
        sf.write(dest, x, 24000, subtype='PCM_16')
        clips.append(x)
        audition_sources.append(dict(label=name, source=str(path), source_sha256=sha(path),
            output=str(dest), output_sha256=sha(dest), start_seconds=0, seconds=10,
            processing='mono24k, RMS .04, peak cap .95, 5ms endpoint fades; no pitch/time/text modification'))
    comparison = OUT/'20秒对照_前原声后新方案.wav'
    sf.write(comparison,np.concatenate([clips[0],np.zeros(7200,dtype=np.float32),clips[1]]),24000,subtype='PCM_16')
    save(OUT/'试听来源.json',dict(path=str(comparison),sha256=sha(comparison),seconds=20.3,
        order='first10s target original, .3s silence, then10s stronger t6 conversion',sources=audition_sources,
        conversion_input=selected['source_path'],conversion_input_sha256=selected['source_sha256'],
        note='Generic TTS reads ASR-derived target text, then conversion. Target original is comparison only; no target-to-target conversion. Different speaking rates; excerpts are not word-aligned. ASR-derived text has not been human proofread.'))
    decision = dict(status='pc_benchmark_complete',date='2026-10-03',
        preferred_candidate='Seed-VC V1 stronger preset + Track6 first8s +30steps/CFG0.7',
        family_note='Checkpoint filename contains v2; this uses V1 inference.py/preset, not V2 AR+CFM inference_v2.',
        candidate_source_revision=strong['source_revision'],config=strong['config'],config_sha256=strong['config_sha256'],
        reference=pcm_records['t6_8s'],assets=strong['assets'],parameter_counts=strong['parameter_counts'],
        total_loaded_parameters=sum(strong['parameter_counts'].values()),seed=20261003,fp16=True,
        diffusion_steps=30,cfg=.7,length_adjust=1,weights_finetuned=False,
        metrics_on_five_new_inputs=metrics,original_input_mean_asr_cer=float(np.mean(cergroups['validation_source'])),
        original_input_maximum_asr_cer=max(cergroups['validation_source']),
        measured_integrity=dict(new_conversions=len(integrity),all_hashes_match=True,all_finite_nonsilent=True,
            maximum_duration_error_seconds=max(r['duration_error_seconds'] for r in integrity),
            outputs_with_clipping=sum(r['clipped_fraction']>0 for r in integrity)),
        offline_pc_rtf_range=[min(r['offline_pc_rtf'] for r in fresh_strong['files'] if r['reference_name']=='t6_8s'),
            max(r['offline_pc_rtf'] for r in fresh_strong['files'] if r['reference_name']=='t6_8s')],
        original_rvc_preserved=True,backup='pool24s: higher identity mean but worse naturalness/content mean on fresh set',
        source_speaker_enrollment=False,source_validation_used_for_training=False,audio_uploaded=False,
        subjective_acceptance=False,causal_streaming=False,board_deployed=False,board_end_to_end_latency_measured=False,
        active_phase_jobs=0,
        next_step='One short selected-candidate perceptual check; if acceptable, design causal lightweight student and budget PS/PL compute. If target timbre is still inadequate, improve teacher first.',
        limitations=['Five fresh clips are small-sample validation, not statistical/general-speaker acceptance.',
            'FLEURS has gender metadata, not person IDs; two female clips do not establish two different female people.',
            'No proof that public clips were absent from upstream pretraining; absent from this project target training.',
            'Cosine and UTMOS are diagnostics, not percent likeness or human acceptance.',
            'Strong t6 does not dominate every single clip or older same-text MFCC-DTW.',
            'Offline GPU file RTF is not streaming latency or evidence of 7020 feasibility.'])
    decision_path=OUT/'阶段候选决策.json'
    if decision_path.exists():
        historical=read(decision_path)
        if historical.get('human_result'):
            for key in ['human_result','human_feedback','preferred_candidate_accepted','next_step']:
                if key in historical:decision[key]=historical[key]
            decision['subjective_acceptance']=historical.get('subjective_acceptance',False)
    save(decision_path,decision)
    save(OUT/'最终文件完整性.json',dict(status='complete',files=integrity))
    labels = ['现有RVC120轮','Seed较强版：Track6开头8秒','Seed较强版：拼接24秒参考']
    table = '\n'.join(f"| {label} | {r['mean_wespeaker_cosine']:.4f} / {r['minimum_wespeaker_cosine']:.4f} | {r['mean_utmos']:.3f} / {r['minimum_utmos']:.3f} | {r['mean_asr_cer']:.4f} / {r['maximum_asr_cer']:.4f} |" for label,r in zip(labels,metrics))
    counts = strong['parameter_counts']
    report = f'''# 下一阶段结果：参考选择、较强教师与新增中文验证

日期：2026-10-03。该阶段所有任务已经完成，没有后台训练、转换或下载任务。本报告优先于上一阶段“接下来控制参考/试较强模型”的计划。

## 结论

暂选 **Seed-VC V1较强配置 + Track6开头8秒参考 + 30步/CFG0.7** 作为下一步教师候选。在新增五段中文输入上，它的人物身份评分平均/最差、自然度预测平均/最差以及内容识别错误平均/最差均优于现有RVC候选。但优势没有覆盖每个单独文件，也不能据此宣称听起来已像目标人物。保留原RVC及拼接参考候选，不覆盖原权重。没有针对个人微调Seed权重。

## 实际做了什么

1. 固定原来的三个输入，测试四段独立8秒参考及一段24秒拼接参考：tiny版15段、较强版9段，共24段转换。tiny的中文身份平均分从Track8参考0.7152变为Track6参考0.8107，但仍低于现有RVC的0.8820，说明参考影响较大，单换参考还不够。较强版Track6为0.8952，拼接为0.9168；旧输入自然度均未全面领先RVC。
2. 引入五段此前未用于项目目标训练的新测试输入：AISHELL已知新说话人S0004的两段，FLEURS中文test的两段女声、一段男声。FLEURS没有人物ID，不能当作两个已确认不同的女性。模型上游训练数据是否包含这些公开录音未知。它们不参与目标模型训练、检索或输入人物注册。
3. 固定参数，生成现有RVC五段及两个Seed候选各五段，共15段新增转换。合计本阶段 **39段转换，8个输入音频**。中文身份/自然度最终评估文件共105个，包含历史基准及参考，不是105个新转换或105名说话人。
4. 对全部39段检查文件SHA256、有限数值、非静音、削波、输入输出时长，并复核原始新测试录音未变化。最大时长差{decision['measured_integrity']['maximum_duration_error_seconds']:.6f}秒；削波文件数{decision['measured_integrity']['outputs_with_clipping']}。现有目标素材原始文件保持不变。

## 新增五段输入上的公平对比

| 方案 | 中文身份：平均 / 最低 ↑ | UTMOS：平均 / 最低 ↑ | ASR CER：平均 / 最高 ↓ |
|---|---:|---:|---:|
{table}

中文身份是WeSpeaker中文ResNet34-LM的**原始余弦**，不能解读为百分比相似度；UTMOS为自然度预测，中文域与气声/鼻音等细节仍有盲区。ASR对原始五段也有错误：平均CER {decision['original_input_mean_asr_cer']:.4f}，最高{decision['original_input_maximum_asr_cer']:.4f}；因此转换CER不全是吐字错误，应以配对差异辅助判断。完整逐文件结果在两份validation JSON中。

拼接24秒身份分更高，但自然度和内容平均更差，因此没有只追求身份分最高。较强Track6在原来同文本对比的MFCC-DTW为54.243，现有RVC为43.077（该诊断越低越好）；它也没有在所有诊断上全面胜出。小测试集没有证明任意说话人成功，最终还须听感、多说话人与真实端到端延迟验收。

## 20秒试听的来源

`20秒对照_前原声后新方案.wav`：前10秒是目标人物原声，间隔0.3秒，后10秒是选定新方案。转换输入仍是普通合成声读目标片段的识别文字，然后变换音色；没有把目标原声直接送入转换模型来冒充效果。文字未改写，但原始ASR转写尚未人工逐字核对。两者语速不同，这两个开头片段不是逐词对齐。

只为试听做单声道24k、音量匹配及端点5ms淡入淡出，没有调整音高/语速/文本。另有独立两段10秒文件。原始目标和完整转换输出均保留；来源及SHA256在`试听来源.json`。本次只准备这一条选定版本供必要时最终听感确认，不要求逐版试听。

## 为什么还不能直接放进7020

实加载参数：转换网络{counts['cfm']:,}、长度调整{counts['length_regulator']:,}、人物参考编码{counts['campplus']:,}、声码器{counts['vocoder']:,}、语义编码{counts['semantic_encoder']:,}，合计 **{sum(counts.values()):,}（约3.10亿）**。这次使用V1推理程序；权重文件名虽包含v2，不是新的V2 AR+CFM路径。

电脑GPU离线处理速度不等于连续实时延迟。这里没有验证因果流式、7020推理或板卡端到端延迟，也没有改SD卡、板卡程序或接线。用户无需为本轮重新上电。下一步先确认选定教师的实际音色；若仍明显不像，继续改教师；若接近可接受，再设计因果小型学生、量化和PS/PL运算预算。不能把3.10亿参数管线直接部署成功当作既定事实，也不保证在比赛时限内实现最终质量。

## 可复现记录

固定源码提交`{strong['source_revision']}`，参数seed20261003、FP16、30步、CFG0.7、length1、不启用F0条件/升调。配置SHA256 `{strong['config_sha256']}`；权重仓库固定版本、文件路径和SHA256见`阶段候选决策.json`的assets。音频全部在本机处理，没有上传目标声音。

参考FLOAT WAV在多次运行前重新生成，其PEAK时间戳可能改变字节哈希；历史运行记录按原样保留。已独立验证当前解码参考与“原片段→单声道→RMS0.04”的确定规则逐样本完全一致，并记录稳定的浮点PCM哈希，见`reference_pcm_integrity.json`。原始素材哈希与转换结果哈希核对通过。

`reference_matrix_cross_eval.json`/`reference_matrix_content_eval.json`冻结旧输入对照；`validation_cross_eval.json`/`validation_content_eval.json`冻结新增输入结果。`阶段候选决策.json`保存临时选择、限制和下一步；`最终文件完整性.json`保存39段检查。源码脚本位于D盘工程的neural_reference目录。
'''
    if decision.get('human_result')=='rejected':
        report=report.replace('## 结论\n\n','> 后续听感验收：用户明确反馈“还差一些，有点不自然；明显不像”。下文暂选候选未通过验收，不应直接进入学生蒸馏或板卡部署。\n\n## 结论（试听前的自动筛选结果）\n\n',1)
    (OUT/'阶段结果说明.md').write_text(report,encoding='utf-8')
    entry = '''### 参考控制、较强教师及新增中文验证（本阶段已完成）

已完成39段新转换：原三输入24段参考/模型控制，新增五输入15段新旧方案对比。暂选Seed-VC V1较强版、Track6开头8秒参考、30步/CFG0.7作为教师候选；它在新增五段上的中文身份均值/最低0.8854/0.8656（RVC0.8699/0.8055）、UTMOS均值/最低3.512/3.083（RVC3.392/2.654）、ASR CER均值0.1676（RVC0.1743）。拼接参考身份更高但自然度/内容更差，保留备用。不能把评分当百分比或听感验收，新候选不是每段/每个诊断都领先，尚未获得用户听感反馈。

新增输入为AISHELL S0004两段及FLEURS中文test两段女声/一段男声；FLEURS无人物ID，不能断言两个不同女性。未进入项目目标训练或注册，也不能证明不在上游预训练中。Seed没有针对个人微调。原RVC保留；本阶段全部任务已结束，无后台任务、音频上传、SD修改或板卡部署。较强版整条实际管线约3.10亿参数，尚非因果流式，电脑离线GPU速度不代表7020实时。

报告：`D:\\总进度\\目标人物分析\\SeedVC下一阶段\\阶段结果说明.md`；决策及固定权重/参数：同目录`阶段候选决策.json`。已准备约20秒唯一短对照（前10秒目标原声、后10秒普通合成声经新方案转换），原始素材保留；需要时只确认选定版本，避免逐版试听。下一步以实际音色确认教师，再做小型因果学生与PS/PL预算；若仍不像，先改教师。无需补录、接线或板卡上电。学习线不变。本条覆盖下文历史“下一步试更强模型/任务运行中”的状态。

'''
    handoff = Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md')
    text = handoff.read_text(encoding='utf-8')
    marker = '## 最新工程进展：2026-10-03（优先于下文原有阶段计划）\n\n'
    if '### 参考控制、较强教师及新增中文验证' not in text:
        if marker not in text:
            raise RuntimeError('Handoff anchor missing')
        handoff.write_text(text.replace(marker,marker+entry,1),encoding='utf-8')
    status_path = BASE.parent/'PROJECT_STATUS.md'
    text = status_path.read_text(encoding='utf-8')
    status = '''## Latest: stronger teacher and new-input validation — 2026-10-03

- Completed39 new conversions:24 controlled-reference outputs on3 old inputs and15 outputs on5 fresh Mandarin clips (S0004 x2; FLEURS female clips x2 and male clip x1, no FLEURS speaker IDs). Preferred provisional teacher: Seed-VC V1 stronger Whisper/BigVGAN preset, Track6 first8s,30steps/CFG0.7, fixed seed20261003. On fresh5, Mandarin raw cosine mean/min0.8854/0.8656 vs frozen RVC0.8699/0.8055; UTMOS mean/min3.512/3.083 vs3.392/2.654; ASR CER mean0.1676 vs0.1743. Pool24s has higher identity but worse naturalness/content means; preserve backup. Not every clip/diagnostic improves; no subjective acceptance.
- All39 output hashes, finite/non-silent samples, duration and clipping checked. Original target/source files preserved. No source enrollment, target training on fresh sources, personalized Seed fine-tuning, audio upload, SD change or board deployment. All phase jobs complete, none running. Full stronger pipeline310,246,816 parameters, noncausal offline PC reference; not7020-ready or measured live latency. Weight filename's v2 is not inference_v2 AR+CFM. One20.3s selected audition prepared (target original10s + generic-TTS-to-target conversion10s); no repeated per-variant listening required. Next: confirm teacher timbre, then budget/design causal student PS/PL, or improve teacher if likeness still fails. Board power-on is not needed. Full report/decision: `D:\\总进度\\目标人物分析\\SeedVC下一阶段`. This supersedes earlier pending-phase plans below.

'''
    if '## Latest: stronger teacher and new-input validation' not in text:
        status_path.write_text(text.replace('# Zynq-7020 Low-Latency Voice Conversion Project\n\n','# Zynq-7020 Low-Latency Voice Conversion Project\n\n'+status,1).replace('- The board is currently powered on with live loopback running. End-to-end latency is not yet measured, and voice conversion is not yet implemented.','- Live bypass was previously verified. User subsequently planned physical power-off due heat; current physical power and clean Linux shutdown are unconfirmed. End-to-end latency remains unmeasured; target neural conversion is not deployed.'),encoding='utf-8')
    print(json.dumps(dict(status='complete',conversions=len(integrity),total_loaded_parameters=sum(counts.values()),
        audition=str(comparison),report=str(OUT/'阶段结果说明.md'),
        clipping_outputs=decision['measured_integrity']['outputs_with_clipping'],metrics=metrics),ensure_ascii=False))

if __name__=='__main__':
    main()
