from pathlib import Path
import datetime
import json

base = Path(__file__).resolve().parent
native = base.parent / 'board_support/native_llvc_20261005'
now = datetime.datetime.now().isoformat()
live = {
    'time': now,
    'board_mode': 'live neural conversion: wide192_shallow2_target_anchor; awaiting human quality feedback',
    'model_sha256': 'eaa08fd14eafdfceb34bd4f9fbbd82f1c4aa870e783df7e596d48a46f5af2361',
    'board_model': '/home/root/native_llvc_trial_20261005/wide192_shallow2_target_anchor_selected.f32',
    'board_runtime': '/home/root/native_llvc_trial_20261005/native_llvc_wide192_shallow2_meter_arm',
    'board_helper': '/home/root/native_llvc_trial_20261005/board_neural_wide192.sh',
    'pids_at_observation': {'capture': 26793, 'convert': 26794, 'playback': 26795},
    'observed_live_status': {
        'input_samples': 5221232, 'output_samples': 5221216, 'chunks': 25102,
        'mean_compute_ms': 11.069815, 'max_compute_ms': 19.537692,
        'compute_deadlines_missed': 161, 'finished': False,
        'input_gain': 1, 'output_gain': 1,
        'playback_underruns_total': 1, 'playback_underrun_ms': 146.116,
        'new_playback_underruns_between_98s_and_326s_status': 0,
        'underrun_occurrence_time_unknown': True,
    },
    'mixer': {'Capture': 43, 'Headphone': 119, 'Playback': 222},
    'original_feedback_accepted': True, 'repeat_original_verification_required': False,
    'original_audio_mixed_into_output': False, 'microphone_recorded': False,
    'source_enrollment': False, 'ps_arm_inference': True, 'new_pl_acceleration': False,
    'acoustic_latency_measured': False, 'target_quality_accepted': False,
    'human_new_model_feedback_pending': True, 'project_complete': False,
    'known_gap': 'Male source F0 remains near source rather than teacher; target identity incomplete.',
    'board_numeric_validation': json.loads((native / 'wide192_trained_board_numeric.json').read_text(encoding='utf-8')),
}
(native / 'wide_live_trial_evidence.json').write_text(json.dumps(live, ensure_ascii=False, indent=2), encoding='utf-8')
for name in ['continued_refinement_evidence.json', 'realtime_stage_evidence.json', 'noise_refinement_stage_evidence.json']:
    p = native / name
    obj = json.loads(p.read_text(encoding='utf-8'))
    obj['current_state_updated_at'] = now
    obj['board_mode'] = live['board_mode']
    obj['stage'] = 'Wide192 shallow2 neural live trial running; new human audition pending'
    obj['wide_live_trial'] = live
    obj['older_neural_trial_active'] = False
    obj['active_diagnostic_recording'] = False
    obj['historical_fields_notice'] = 'Prior experiments and feedback retained below are historical; latest current state is wide_live_trial.'
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

doc = Path('D:/总进度/原声验收后_模型改进_2026-10-05.md')
text = doc.read_text(encoding='utf-8')
text = text.replace('当前板子仍是pcm_bridge_bypass原声；没有转换模型，没有麦克风诊断录音。最近原声进程26078/26079/26080，需继续工作时读实时进程确认。',
    '当前板子已切到wide192_shallow2_target_anchor神经模型实时转换，原声直通已停；没有麦克风诊断录音。新模型实际听感尚待用户反馈。观察时采集/转换/播放进程为26793/26794/26795，继续工作时读取实时状态确认。原声验收是历史已通过的基线，不能当作新模型验收。')
text = text.replace('新运行程序上传仅用于文件运算，不代表切换到现场转换。', '新运行程序先通过板上文件数值/速度核对，随后已明确切换到现场实时转换。')
text = text.replace('先读最后的continued_refinement_evidence.json及本文件，检查新结构是否训练完成；', '先读wide_live_trial_evidence.json及本文件。新结构训练已完成、已部署且实时试听待反馈；')
text += '''

## 最新实际部署与运行（本节覆盖前面历史状态）

新模型800步权重已上传，SHA256为eaa08fd14eafdfceb34bd4f9fbbd82f1c4aa870e783df7e596d48a46f5af2361。运行程序native_llvc_wide192_shallow2_meter_arm，操作脚本board_neural_wide192.sh，都在板子/home/root/native_llvc_trial_20261005。神经模型连续处理麦克风并输出到音箱，不录音等待、不混原声、不做额外音高预处理；输入/输出数字增益均为1。PS双核运行，本轮没有增加PL硬件。

固定中文B的4.32秒文件在实际ARM推理3.77209秒，平均11.3128ms/块、最大14.9591ms；输出69120样本，与电脑相同权重参考归一化误差3.378887e-7、最大绝对误差2.08616e-7。文件运算本身不等于实时链路验收。

实际麦克风实时模式后续观察已处理5221232样本，约326.3秒；25102块平均11.069815ms、最大19.537692ms、161块计算超过13ms。三个进程仍运行。播放日志总共出现一次146.116ms缓冲不足，发生时间未单独记录；约98秒至326秒两次观察间未新增。不能声称零卡顿或已经测量端到端延迟。音量沿用已验收原声Capture43/Headphone119/Playback222。尚未收到新模型人声清晰度/噪声反馈，目标音色与任意人转换仍未完成，尤其男声基频仍近输入源。

下一步是用户对这个新候选现场说两三句，反馈清晰度和杂音；无需再校验原声接线、反复调增益或要求用户录音。若实时故障，可用board_original_accepted.sh恢复已验收原声。总进度旧续接文件仅作历史详细记录，当前状态以本节及wide_live_trial_evidence.json为准。
'''
doc.write_text(text, encoding='utf-8')
older = Path('D:/总进度/7020实时小模型工程续接_2026-10-05.md')
with older.open('a', encoding='utf-8') as f:
    f.write('\n\n## 最新状态补充：原声验收后新模型已实时上板\n\n详见同目录《原声验收后_模型改进_2026-10-05.md》最后一节。已完成E192/D96、2层结构3200步重建及800步目标转换训练，实际部署到7020并实时运行，保留Capture43/Headphone119/Playback222。新模型待用户清晰度/杂音反馈，目标音色尚未完成。约326秒实时观察平均11.07ms/13ms块，日志一次146ms缓冲不足、两次观察间未新增；不可宣称零卡顿。旧9200模型、原声直通、诊断录音都不是当前运行模式。以board_support/native_llvc_20261005/wide_live_trial_evidence.json为当前证据。\n')
print('Live evidence and engineering handoffs updated.')
