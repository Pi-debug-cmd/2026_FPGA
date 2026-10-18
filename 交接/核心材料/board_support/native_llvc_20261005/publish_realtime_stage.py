"""Engineering handoff update; separate speed proof from quality acceptance."""
from pathlib import Path
import json,hashlib,datetime
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    baseline=read(ROOT/'actual_arm_numerical_checks.json')
    cadence=read(ROOT/'paced_stream_result.json')
    duplex=read(ROOT/'duplex_mic_compute_status.json')
    quality=read(PROJECT/'board_budget_20261005/small96_identity_training/heldout_screening.json')
    rows=[]
    for path in [ROOT/'native_llvc_small96_stream_arm',
                 PROJECT/'board_budget_20261005/small96_identity_training/small96_trained.f32',
                 ROOT/'board_neural_live.sh',ROOT/'asound_neural.conf',ROOT/'live_watchdog.py']:
        rows.append(dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path)))
    full=next(c for c in baseline['cases'] if c['case']=='real_16000')
    status=dict(stage='Experimental native small96 live chain; human listening pending; NOT final quality acceptance',
        created_local_date='2026-10-05',full_original_model=full,student=dict(enc_dim=96,dec_dim=48,encoder_layers=8,
            decoder_layers=1,heads=8,head_dim=6,chunk_samples=208,lookahead_samples=16,rate=16000,
            parameters=173456,training_after_structured_initialization_steps=6400,weights_bytes=740939,
            actual_board_one_second_seconds=.854141,mean_chunk_ms=11.0842,max_chunk_ms=11.6619,
            peak_rss_kib=2784,actual_migration_nrmse=2.164881516364403e-5,
            source_speaker_enrollment=False,quality_accepted=False),
        corpus_manifest=str(PROJECT/'board_budget_20261005/student_corpus/paired_manifest.json'),
        corpus_source_seconds=346.44975056689344,train_speakers=12,validation_speakers=2,test_speakers=2,
        native_teacher_source_timing=True,teacher_waveform_time_warp=False,target_track9_training=False,
        cadence=cadence,duplex_mic_compute_with_silent_playback=duplex,validation=quality['summary'],
        auxiliary_wespeaker_gradient_used=True,wespeaker_is_no_longer_independent_identity_evaluation=True,
        acoustic_latency_measured=False,continuous_final_quality_accepted=False,
        pc_inference_in_live_path=False,neural_pl_acceleration_loaded=False,
        microphone_voice_files_saved=False,boot_or_sd_partition_changed=False,artifacts=rows)
    if (ROOT/'actual_live_status.json').exists():status['latest_live_status']=read(ROOT/'actual_live_status.json')
    (ROOT/'realtime_stage_evidence.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
    m=read(ROOT/'deployment_artifacts.json');m['current_small_model_stage']='realtime_stage_evidence.json'
    m['status']='Original full ARM migration PASS / original realtime FAIL; new small96 experimental native live IO; quality NOT accepted'
    (ROOT/'deployment_artifacts.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
    p=read(ROOT/'board_preflight_actual.json');p['actual_full_model_arm_execution']=True
    p['current_stage']='Full baseline verified; separate small96 experiment and live IO, see realtime_stage_evidence.json'
    (ROOT/'board_preflight_actual.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
    document=r'''# 7020实时小模型工程续接（2026-10-05）

## 总目标及验收边界

任意未预先登记的输入者对麦克风讲话，音箱低延迟输出同一事先采集的目标人物声音。核心计算必须在野火Zynq7020，中文内容正确、音色接近且自然。电脑仅作训练/离线教师。不能用先录整句话再处理、电脑转换后板子播放、隐藏原声直通或简单升调替代。
当前只是实时小模型工程试验，目标音质尚未完成。用户想现场讲话听板上效果，不同意以5秒预录等待两分多钟替代实时。因此已取消那次预录，mic_original.wav、mic_converted.wav没有生成。

## 状态改变必须看清

旧完整LLVC的20步检查点，已在真实ARM执行四项数值测试并通过。1秒真实中文处理31.2346秒，平均405.634毫秒/13毫秒块，RSS17060KiB。这个完整模型仍不实时、也没有目标音质验收。
本轮没有让这个完整模型突然实时，而是优化程序并缩小、重新训练了一个独立学生模型。它不是CosyVoice3教师②/C，也不能宣称同样音质。
最后采用E96、D48、8层膨胀编码器、1层8头attention解码器（每头6维），仍208样本/块与16样本有限前看，16kHz单声道。173456个参数，导出文件740939字节。
完整权重无需输入者录制参考音频。固定目标条件已含在学习权重/预计算label里，现场不读取目标人物WAV。

## 程序加速过程

1. 保留原native_llvc.cpp/native_llvc_arm和其SHA，不覆写数值验证基线。
2. 新矩阵核按输出4通道打包，复用同一权重同时计算4帧；两颗Cortex-A9分担输出通道；持久工作线程避免逐层创建线程。Q/K/V使用永久原权重视图及缓存，去掉每块拷贝临时矩阵。
3. 单核原完整结构纯音约161毫秒/块；双核约106毫秒/块。真实1秒耗时8.19385秒，仍不实时。原结构数值NRMSE9.728e-6。
4. E128/D64、E96/D48候选按attention每头均匀选择通道，并保留encoder成对通道，让grouped投影对应；全部模型张量严格匹配加载。只是结构初始化，不是质量保真。
5. 编码器使用环形历史缓冲，避免每13毫秒复制所有膨胀历史；depthwise和输出转置卷积使用显式NEON；没有fast-math或查表激活近似。
6. E128环形版真实1秒1.08251秒，平均14.0495毫秒，最慢14.6663毫秒，不够。
7. E96环形版初始化真实1秒.844857秒，平均10.9635、最慢11.5337毫秒，数值NRMSE3.6675e-6。
8. 6400步训练后E96实板1秒.854141秒，平均11.0842、最慢11.6619毫秒，RSS2784KiB；与该检查点PyTorch流式参考NRMSE2.16488e-5、最大绝对差4.46162e-8。不是与旧大结构波形对照。

编译器是VivadoSDK2018.3的ARM hard-float GCC，-O3/-std=c++11/-mcpu=cortex-a9/-mfpu=neon/-mfloat-abi=hard/-static。
静态线程库必须完整链接：-Wl,--whole-archive -lpthread -Wl,--no-whole-archive。仅-pthread会遗漏部分弱引用条件变量函数，实板曾报std::system_error；已经修正。
Windows流接口测试需_setmode stdin/stdout为_O_BINARY，避免换行翻译改变PCM字节数。这不涉及ARM音频算法。

## 新训练数据与教师

数据：board_budget_20261005/student_corpus。源AISHELL-3官方仓库固定f20d5db4a31fe779ef07bb1af4ea92da5c786622，Apache-2.0。
先排除之前55条发音诊断中所有说话人，再按固定规则选择16个新说话人，每人4条：12人/48条训练，2人/8条validation，2人/8条test。男女各半，原始64段总346.44975秒，覆盖8–20字句子。按拼音覆盖选句，选择在推理前冻结。
源文件原始44.1k，训练前mono/resample16k；人物参考仍target_t6_8s.wav，SHA4651ab56a9b285c0d645bd6f0b94f7987e6ed8bd5171e54c37048b436e177c8f。Track9没有用于训练/条件。
教师CosyVoice3原生VC：真实源波形→源speech tokens→固定目标条件→flow/HiFT；未经过ASR/TTS文本替代，未对教师做波形节奏拉伸。固定人物前端缓存一次，每个源独立提取自己的token。
原生教师输出对源只存在最后token帧的长度差。训练仅末尾trim/pad（必须差<=100ms），没有按文本强制对齐，也没有拉伸整段。教师音频只做幅度归一化约.08RMS/.9peak，不代表全部人工听过。

## 小模型训练

第一轮2400步：从E96结构初始化开始，GPU训练48条源/原生教师对。batch2，208*154样本窗口，随机声压增益.35–1.35；前8192样本作为历史热身不计算损失。eval模式避免dropout，但允许训练梯度。
损失：三尺度256/512/1024 STFT和80维log-mel；已有ContentVec/HuBERT前9层的固定源内容特征损失；400步后加3个小周期判别器（2/3/5）LSGAN及特征匹配。
第一轮FP16梯度非有限，已改FP32训练并禁用GradScaler。FP322400步约228.45秒，训练与16条held-out真正流式输出完成。
第一轮验证：152字，源5处/教师9处/学生20处字符编辑；test147字，源6/教师8/学生32。这个学生没有获得音质认可。

第二轮从2400步模型继续4000步（共6400步结构后训练），lr1e-4，加强源内容特征权重6，并增加固定目标说话人特征损失3。因为第一轮错误，不能声称第一轮test仍是之后调参的盲测集；后续只对validation作调试，旧test输出保留诊断，最终仍需新的输入者验证。
说话人损失：从现有WeSpeaker中文ResNet34-LM ONNX精确重放为可微Torch模型，权重不变。Torch/ONNX参考NRMSE7.25435e-7，波形梯度有限且非零；用于离线训练，不部署7020。
关键：WeSpeaker已用于优化损失，不能继续当独立音色审核，更不能用其cosine宣称百分比相似度或人耳通过。仍需人工判断自然度与目标音色，独立ASR也不是发音验收。
第二轮4000步约475.87秒，导出small96_trained.f32。validation学生22编辑/152字（源5、教师9），比第一轮20没有改善；训练用WeSpeaker平均cosine.6961（第一轮.4433），仅辅助诊断，不能视为独立改善证据。没有把它标记合格。

## 真正持续输入的流接口

native_llvc_small96_stream_arm --stream MODEL STATUS_JSON
stdin/stdout都是S16_LE/mono16k原始PCM。初始仅收224样本即可生成208样本，之后每208样本生成208样本。环形状态和有限前看常驻，无整句缓存、不存用户语音、不靠电脑计算。
EOF0/1/16/207/208/209/224/416/16000样本与同程序文件路径PCM输出逐字节一致；先发送224样本且保持输入打开，即收到首208输出，证明不等完整句子。
实板13毫秒节拍测试使用既有公开FLEURS10.38秒：166080输入/166080输出、799块，平均11.088848、最慢11.605092毫秒，0次计算超预算，生产者最长写入.0953毫秒，没有积压。该测试初始化权重，不是麦克风音质验收/最终端到端延迟。
实际麦克风转换丢弃输出、同时播放静音的10秒双工接口测试：160000入/出、770块，平均11.134512、最慢12.093366毫秒，0次计算超预算，ALSA日志无错。没有保存用户声音文件，也没有进行转换声音试听。

## 官方驱动格式桥和现场状态

直接aplay mono16k/S16_LE失败（xilinx-i2s_playback hw_params -22）；旧官方路径S24_LE/44100/stereo可用。
独立asound_neural.conf强制两侧底层mmap_emul->hw:0,0/0,1使用S24_LE、2声道、44100；plug向模型桥接16k/mono/S16。ALSA_CONFIG_PATH只对本次脚本生效，没有改/etc/asound.conf。
初次全链路39?启动缓冲之前：--start-delay=13000只留一块，实际出现播放underrun约14ms。改为39000（约3块）仍用832样本/52ms容量，必须继续核对播放日志。不能把“单块计算11ms”说成“端到端11ms”。
现场底层查询实测S24_LE、2声道、44100，period_size576、buffer_size2304。训练/模型接口仍16k。
board_neural_live.sh start|stop|status 控制本次capture/convert/playback；只操作自己的PID/FIFO，原music-button和voice-live暂时停止，但启动配置未改。
live_watchdog.py检查进程退出、持续平均超13ms及试验保守85℃温度阈值并停止链路（85不是厂商认证上限）。
默认新版现场权重small96_step6400.f32，SHA dbe07ea6d3f9dba5d81e8fdd44fa84b0426966fe67f684546e91946a97681ce8。源/模型/程序UART传输SHA验证通过；COM8/115200控制，230400二进制传输后恢复115200。

## 路径与恢复

主工程D:\Tools_FPGA\workspace\voice_conversion_zynq7020
原生/部署目录board_support\native_llvc_20261005；板上/home/root/native_llvc_trial_20261005。
训练代码neural_reference\prepare_board_student_corpus_20261005.py、make_board_student_pairs_20261005.py、train_board_student_20261005.py、differentiable_speaker_20261005.py、screen_board_student_20261005.py。
原生生成/检查make_fast_build.py、prepare_small_geometry.py、make_ring_build.py、make_stream_build.py、verify_live_adapter.py；所有候选独立命名，原完整模型基线不动。
结果board_budget_20261005\student_corpus、small96_training、small96_identity_training及各log。第二轮最终检查点checkpoint_step4000.pt（resume来自第一轮2400）。
停止现场：sh /home/root/native_llvc_trial_20261005/board_neural_live.sh stop。
恢复原声：/usr/local/bin/voice-live.sh start bypass。该路径只是原声直通，不能叫目标人物转换；不带bypass默认旧升调模式。
不改变SD分区、boot bitstream、开机服务或野火原件；当前神经运算在PS双核ARM，PL是原官方音频外设，自研HLS核未加载。比赛FPGA核心加速仍需后续工程。

## 接下来

先完成现场连续输出的无欠载检查，再让用户正常讲话，明确这是试验版，不能说音色/发音已经完成。用户听感可决定是否保留声音候选；严禁以训练使用的声纹评分覆盖人工否定。
质量需要继续改进，尤其中文错字和未见输入者稳定性。扩大/改进结构需先保持板预算，不能退回先无约束优化电脑大模型。
需要独立新说话人测试、音箱录回/测量实际端到端延迟、温度长时稳定及后续PS/PL加速集成；不要用容量换取不断增长延迟。
同文本对比继续“我的校园很美，走近大门就能看见宽阔的操场。”；原声、普通输入、转换必须分开，不能换台词后让用户猜比较。
2026-10-04工程交接书保留历史教师/失败路线背景；本文件覆盖“尚无ARM程序/学生只20步/需要预录等待两分钟”的旧阶段状态。
'''
    document=document.replace('初次全链路39?启动缓冲之前','初次全链路调整启动缓冲之前')
    path=Path('D:/总进度/7020实时小模型工程续接_2026-10-05.md')
    path.write_text(document,encoding='utf-8')
    current=Path('D:/总进度/7020原生小模型部署进度_2026-10-05.md')
    current.write_text('# 当前工程状态（2026-10-05）\n\n已将原完整模型从31.23倍慢的实板基线推进到独立E96实时小模型，实际1秒计算.854秒。\n当前模型已训练6400步，仍有中文错误、音色未验收；现场IO联调/试听不是最终成果。\n\n最新详细工程续接文件：'+str(path)+'\n证据入口：'+str(ROOT/'realtime_stage_evidence.json')+'\n\n'+current.read_text(encoding='utf-8'),encoding='utf-8')
    print('Published engineering continuation with explicit quality limits.')
if __name__=='__main__':main()
