"""Publish measured board results and preserve the earlier preparation snapshot."""
from pathlib import Path
import json, hashlib

root = Path(__file__).resolve().parent
checks = json.loads((root / 'actual_arm_numerical_checks.json').read_text(encoding='utf-8'))
real = next(c for c in checks['cases'] if c['case'] == 'real_16000')
profiles = []
for name in ['actual_arm_profile.jsonl', 'actual_arm_profile_tone.jsonl']:
    rows = [json.loads(line) for line in (root / name).read_text().splitlines()]
    stats, entries = rows[0], rows[1]['profile']
    chunks = stats['chunks']
    dense_ms = sum(v['exclusive_ms'] for k, v in entries.items() if k.startswith('linear_')) / chunks
    exclusive_ms = sum(v['exclusive_ms'] for v in entries.values()) / chunks
    profiles.append(dict(file=name, stats=stats, dense_ms_per_chunk=dense_ms,
                         other_ms_per_chunk=exclusive_ms-dense_ms,
                         exclusive_sum_ms_per_chunk=exclusive_ms,
                         fractions= {k: v['exclusive_ms'] / (chunks * exclusive_ms) for k,v in entries.items()},
                         output_bit_identical_to_verified_baseline=True))
summary = dict(actual_board_execution=True, profile_cases=profiles,
               profiling_is_a_separate_binary=True, baseline_source_unchanged=True,
               actual_model='checkpoint_step20.pt; 2 sentences, 20 steps, quality unaccepted',
               continuous_real_time_verified=False,
               current_realtime_gate='FAIL: 13 ms audio costs about 405 ms baseline compute',
               native_dense_kernel_theoretical_ms=8.52428,
               ideal_dense_replacement_plus_measured_other_ms=8.52428+profiles[1]['other_ms_per_chunk'],
               hybrid_estimate_warning='Mixed fixed-point PL/FP32 PS estimate only; excludes transfers, conversion, driver, DDR stalls, audio IO and quantization quality; not measured hybrid performance.',
               user_microphone_trial_cancelled=True,
               next_stage='Reduce/accelerate full model under 13ms budget, then validate target quality and continuous microphone IO.')
(root / 'actual_arm_performance_diagnosis.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
manifest_file = root / 'deployment_artifacts.json'
manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
manifest['status'] = 'ACTUAL ARM execution and numerical migration PASS; continuous real-time FAIL; target speech quality UNACCEPTED'
manifest['actual_board'] = dict(port='COM8', cpu_mhz=666.666, total_ram_kib=1029284,
                               remote_dir='/home/root/native_llvc_trial_20261005',
                               full_package_sha_verified=True,
                               actual_arm_checks='actual_arm_numerical_checks.json',
                               one_second_case=real,
                               microphone_recording_trial_cancelled=True,
                               continuous_real_time_verified=False,
                               target_quality_accepted=False)
manifest['performance_diagnosis'] = 'actual_arm_performance_diagnosis.json'
manifest['profile_artifacts'] = []
for name in ['make_profile_build.py', 'native_llvc_profile.cpp', 'native_llvc_profile_arm', 'actual_arm_profile.jsonl', 'actual_arm_profile_tone.jsonl']:
    p=root/name
    manifest['profile_artifacts'].append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
manifest_file.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')

readme = root / 'README.md'
old = readme.read_text(encoding='utf-8')
snapshot = root / 'README_before_actual_board_run.md'
if not snapshot.exists(): snapshot.write_text(old,encoding='utf-8')
header = '''# 7020原生推理：实板执行成功，实时性能未达标（2026-10-05）

本文首部为当前状态。下面保留的准备记录已被本次实板结果覆盖，不能继续据其声称“尚未上板”。

## 已取得的实板证据

- 用户确认接线、上电后，COM8已取得root shell。Linux5.15/PetaLinux2022.2，ARMv7，CPU实际666.666MHz，内存约1GiB。
- 完整模型/静态ARM程序经UART传输并核对SHA256，独立放在 `/home/root/native_llvc_trial_20261005`。
- 静音416样本、纯音1000样本、209样本尾块和真人中文16000样本四项均在实际7020执行；与原PyTorch参考数值对照均通过。
- 真实1秒音频推理31.2346秒，77个块平均405.634毫秒、最慢414.573毫秒；峰值RSS17060KiB。
- 真实源NRMSE7.88898e-6、最大绝对差5.86215e-9，只证明移植计算一致，不证明目标音色/中文发音合格。
- 该1秒测试温度峰值66.196℃；短性能剖析后约63.4℃。没有给出厂商安全温度认证。
- ARM使用的仍是2句20步LLVC未接受检查点；不是认可的电脑教师②，也不是新的CV3转换C。电脑效果不能据此当作板上效果。

## 为什么取消麦克风录音试听

用户要求实时转换，明确质疑先录5秒再等两分多钟的做法。该试听已取消：没有启动用户5秒录音，没有生成mic_original.wav或mic_converted.wav。
只做过1秒ALSA格式探测，得到32000字节原始采样；它不是用户转换/音质验收。
每块输入仅13毫秒，却需要约405毫秒计算，连续输入会持续积压。不能用预录试听、丢弃大段输入、加大缓冲来宣称实时完成。

## 分阶段实际计时

新增独立 `native_llvc_profile_arm`，不覆盖已验证程序、权重与源码。416样本静音和1000样本纯音输出SHA均与已验证基线完全一致。
短测总耗时约394–395毫秒/块。纯音剖析中：
全部密集矩阵约346.20毫秒/块（约87.7%）；其他计算约48.39毫秒/块。
其中8个512×512编码器矩阵约256.57毫秒/块；编码器其余操作约16.96毫秒/块；attention矩阵外操作约11.13毫秒/块；输出卷积约8.95毫秒/块；所有归一化约4.90毫秒/块。
这里使用嵌套计时的exclusive项，避免把子函数重复算入父函数。

现有128路定点HLS矩阵核的理想矩阵预算8.52428毫秒/块仍不是整机实测。
即使简单用该理论值替换346毫秒矩阵，保持其余FP32操作不变，估计仍约56.9毫秒/块，且尚未计入传输/驱动/量化格式转换/DDR等待/音频IO。
因此不能承诺“接上已有矩阵核就实时”；剩余部分和模型结构也需处理，量化后音质还需重新验收。

## 下一阶段验收门槛

1. 先评估完整模型结构、量化和PS/PL分工，让每13毫秒输入块持续按时处理，并留出音频IO余量。2018.3自研HLS与官方2022.2音频工程兼容仍未解决。
2. 速度、实际资源/内存、中文内容保持和目标音色共同决定候选能否保留，不能只优化某一项。
3. 通过后接持续麦克风输入/音箱输出，测实际端到端延迟及欠载；当前没有该实时神经转换链路。
4. 当前没有需要用户再读一句话的操作。后续若需硬件接线或现场验证，再给明确指令。

## 保留与恢复

没有改boot bitstream、SD分区、开机服务配置或原始官方资料；临时停止音乐按键监听/旧音频进程。
短测结束无arecord/aplay/voice_stream/native推理进程。原声回放恢复入口仍为 `/usr/local/bin/voice-live.sh start bypass`（无参数默认升调，不能混淆）。
该恢复是原声直通，不是目标人物转换。不要在用户未要求时自动播放。

证据：actual_arm_numerical_checks.json、actual_arm_profile.jsonl、actual_arm_profile_tone.jsonl、actual_arm_performance_diagnosis.json、deployment_artifacts.json。

---

## 早期准备记录（历史快照，以下旧“未上板”状态失效）

'''
readme.write_text(header+old,encoding='utf-8')
handoff = Path('D:/总进度/7020原生小模型部署进度_2026-10-05.md')
handoff.write_text(header + '\n完整工程历史：D:\\总进度\\ZYNQ7020人声转换项目_工程接力交接书_2026-10-04.md\n'
                  + '当前原生程序与证据目录：' + str(root) + '\n',encoding='utf-8')
print(json.dumps(dict(profile_matrix_ms=profiles[1]['dense_ms_per_chunk'], profile_other_ms=profiles[1]['other_ms_per_chunk'], updated=[str(readme),str(handoff),str(manifest_file)]),ensure_ascii=False))
