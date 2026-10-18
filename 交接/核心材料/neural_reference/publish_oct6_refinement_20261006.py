"""Preserve factual stage evidence, dynamically including finished candidates."""
from pathlib import Path
import json,datetime
base=Path(__file__).resolve().parent;p=base.parent;budget=p/'board_budget_20261005';native=p/'board_support/native_llvc_20261005';dest=Path('D:/总进度/目标音色继续改进_2026-10-06.md')
names=['wide192_causal_pitch_initial','wide192_causal_pitch_trained','wide192_psola_post','wide192_psola_oracle','fargan_teacher_reconstruction','fargan_mapper_v1','fargan_mapper_v2','fargan_cmn_direct','fargan_mapper_perceptual','fargan_mapper_truncated','fargan_mapper_pitchaware','fargan_teacher_source_energy','fargan_teacher_source_energy_periodicity','fargan_mapper_expanded_v8']
records=[]
for name in names:
    r=dict(name=name)
    mos=budget/'phonetic_naturalness'/(name+'.json');screen=budget/name/'heldout_screening.json';decision=budget/name/'decision.json'
    if mos.exists():
        doc=json.loads(mos.read_text(encoding='utf-8'));s=next((s for s in doc.get('summary',[]) if s['kind']==name),None)
        if s:r['mos_diagnostic']=s['mean_predicted_naturalness']
    if screen.exists():
        doc=json.loads(screen.read_text(encoding='utf-8'));s=next((s for s in doc.get('summary',[]) if s['kind']=='student' and s['split']=='validation'),None)
        if s:r.update(hanzi_edits=s['edits'],characters=s['characters'],target_cosine=s['mean_target_cosine'])
    if decision.exists():
        d=json.loads(decision.read_text(encoding='utf-8'));r.update(training_complete=d.get('complete',False),recognizer_used_as_loss=d.get('recognizer_used_as_loss',False),auxiliary_speaker_loss_used=d.get('auxiliary_speaker_loss_used',False))
    records.append(r)
evidence=dict(updated=datetime.datetime.now().isoformat(),feedback='杂音少了，咬字能接受',accepted_baseline='wide192_shallow2_target_anchor',final_target_identity_accepted=False,project_completed=False,board_serial='COM8 115200 root/root',engineering_directory=str(p),candidates=records,source_enrollment=False,target_track9_training=False,test_audio_used=False)
live_path=native/'fargan_v8_live_evidence.json'
if live_path.exists():
    evidence['latest_board_snapshot']=json.loads(live_path.read_text(encoding='utf-8'))
    evidence['v8_live_trial_deployed']=evidence['latest_board_snapshot'].get('v8_live_deployed',False)
    evidence['v8_human_acceptance_pending']=True
feedback_path=native/'v8_human_feedback.json'
if feedback_path.exists():
    evidence['v8_human_feedback']=json.loads(feedback_path.read_text(encoding='utf-8'))
    evidence['v8_human_acceptance_pending']=False
(native/'oct6_refinement_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
table=['|候选/控制组|自然度预测|中文字编辑数/152|目标音色余弦|','|---|---:|---:|---:|']
for r in records:table.append('|'+r['name']+'|'+(f"{r['mos_diagnostic']:.4f}" if 'mos_diagnostic' in r else '待检查')+'|'+(str(r['hanzi_edits']) if 'hanzi_edits' in r else '待检查')+'|'+(f"{r['target_cosine']:.4f}" if 'target_cosine' in r else '待检查')+'|')
text='''# 目标音色继续改进：2026-10-06工程续接

这份文件只记录工程线，是10月5日续接文件的增量。旧文件仍包含原始资料、接线、混音器、模型结构和既有失败路线。不要把本文件中的候选实验误读为已经替换上板。

## 用户目标与最新验收

任意未登记的讲话者，通过麦克风输入，转换为提前提供的目标人物的声音，保持中文内容，尽量自然和低延迟；最终主要推理必须在野火Zynq7020。电脑用于准备素材、教师生成和训练。不得将电脑推理、先录后等待、纯升调、原声直通包装为完成。

最新原话：“明知道有差距为什么不继续改进，杂音少了，咬字能接受”。解释：当前wide192上板试验的底噪、咬字可以作为继续优化的基线，目标人物身份相似度仍未通过。用户要求自行推进，只有确实需要协助、值得试听或完成时才停。不要再要求证明原声通路；原声已验收音量足够、清晰、少杂音。

工程数据全部D盘；不刷SD卡、不动裸物理磁盘、不改启动文件。没有新PL加速，当前全部是PS双核ARM上的软件神经推理，不能声称已完成FPGA计算加速。

## 保留的板端基线

- COM8，115200，root/root。串口访问必须串行；传文件暂切230400后还原115200，脚本校验SHA256。
- 板目录 `/home/root/native_llvc_trial_20261005`；当前运行目录 `/run/voice-neural-live`。
- `board_neural_wide192.sh start|stop|status`；`native_llvc_wide192_shallow2_meter_arm`。
- `wide192_shallow2_target_anchor_selected.f32`，SHA256 `eaa08fd14eafdfceb34bd4f9fbbd82f1c4aa870e783df7e596d48a46f5af2361`。
- 混音器Capture43、Headphone119、Playback222、ADCPCM190、LINPUT1boost1；右路径保持MIC偏置所需状态。输入/输出软件增益1/1。
- 原声恢复助手 `board_original_accepted.sh` 已存在，不需要重验原声。
- 旧版连续运行约10.47小时的检查：平均11.063855ms/13ms，最大26.888497ms，15680块超过13ms；起始的一次播放underrun之外未增加。平均速度足够并不意味着每块都满足截止期；真实端到端声学延迟未测。
- 本轮为了单独测FARGAN曾短暂停止并重启wide。重启后第一次读取为capture29710、convert29711、playback29712，平均11.315447ms/13ms，最大44.865799ms。PID是历史快照，不可盲目kill。后续独立计时还会重启；接续时重新读取状态。

基线离线8个开发验证音频：自然度预测1.6129667，中文编辑7/152，目标音色余弦0.500573。教师3.56968、编辑9/152、余弦0.872531，对照必须查看完整JSON。用户只接受了噪声和字音，未接受最终音色。

## 本轮先尝试的调整及退回原因

1. 因果音高标准化：YIN在4kHz上估计，151个已发生浊音帧形成滚动中值；目标中心193.133Hz来自Track5–8，8帧后开始平滑，无整段未来统计、无输入人物登记。SoundTouch32ms序列/12ms搜索/8ms重叠。板端平均0.881014ms/13ms、最大3.462198ms；首次输出832样本约52ms。float及S16接口、ARM对齐已验证。但音色/字音指标退步，直接接旧模型和重新训练800步均未上板。
2. 自编因果PSOLA仅处理神经网络输出；624样本39ms延迟，非浊音也是延迟后的模型输出，不混麦克风原声。合成正弦、恒等/静音检查通过，但真实语音退步，未上板。
3. 整段Praat PSOLA做上限控制，使用整段音高统计，明确不能用于实时部署。连这个控制也未改善原模型，证明单纯补音高不足。

SoundTouch源码 `neural_reference/SoundTouch_reference`，提交f738b1132ec1fd56efc90367898244cf52d9e6a5，LGPL2.1保留原许可。路径下causal_pitch_*、causal_psola*和board_budget下对应报告完整记录。最初v2的音频实际更新了，但其状态JSON一度因Windows rename不能覆盖而保留v1内容；后已修复，不能拿早期状态JSON当v2实际参数依据。

## 新方向：FARGAN声码器+独立因果音色映射器

流程为：麦克风PCM → 原版LPCNet音频特征提取 → 仅用过去数据自动归一化音高 → 小GRU把频谱变成目标人物的频谱 → 原版量化FARGAN根据特征合成波形 → ALSA音箱。

输入不识别成文字、不合成“普通文本录音”，没有源音频波形旁路，没有把目标录音拼到结果里。保留源特征的能量和浊音相关性是保持说话强弱/清浊，不是混原始波形。

原版每160样本/10ms一帧，特征20维：前18维Bark倒谱，18号为音高坐标，19号为相关性减0.5。音高坐标log2(f0/62.5)-1.5。声码器内部有一帧条件卷积延迟，不能宣传零延迟；实际麦克风到音箱延迟还没测。

原版资料：[FARGAN说明](https://github.com/xiph/opus/blob/main/dnn/torch/fargan/README.md)，[论文](https://arxiv.org/abs/2405.21069)。核心源保留BSD声明。

源码为codeload下载的main快照，不是git克隆，未获得提交SHA，不能杜撰。源码zip SHA256：8a2120b256f3b5816bee9141f4c965826f79e451ab03d8bac1a60811442bebd2。
官方模型包SHA256：a5177ec6fb7d15058e99e57029746100121f68e4890b1467d4094aa336b6013e，与autogen.sh一致。
PyTorch冻结模型SHA256：2eb56f36f71f246174d769658b5712fa81214650bd425cf050c740c8d6b4464c。
精确路径/文件摘要在native目录 `fargan_assets.json`。

### 已证实的7020计算预算

`fargan_probe_arm` 单核独立测试4.32秒固定中文素材：分析均值0.699701ms/10ms，合成7.059407ms/10ms，合计7.759108ms；分析最大1.073484ms、合成最大7.746426ms。此时还没音色映射器，不能说已完成实时转换。

`fargan_mapper_probe_arm` 450帧测试：映射平均0.362411ms/10ms、最大0.673344ms（当时wide仍同时运行，非完全空载）。相加均值约8.12ms，但正式整条流水线必须另外实测，不能只把各模块均值相加当成功。

特征：声码器分析前18倒谱host/ARM最大差2.86e-6。全部特征NRMSE0.00811、大差只在弱/无浊音的音高/相关性；127个双方认可的活跃浊音帧音高坐标最大差0.002516。不能声称全部特征逐位一样。OwnMapper C相对PyTorch归一化+GRU：NRMSE6.48e-8、最大差9.54e-7，ARM已验证。

`native_fargan_mapper_host.exe` 连续PCM stdin→stdout，与同源文件“提取→映射→合成”分步链72000样本逐位相同，SHA256 2ffac9ed8e44bc89c3a5d04fd88a0030bfbb5d4934bb7081806552ae4b7e32f4。独立的板端整链计时/音质检查仍按最新报告确认。

### 声码器上限与当前不足

把已经转换得较好的教师音频提取特征后原样送FARGAN（并非任意人的音色转换），自然度预测2.977731、编辑7/152、目标余弦0.770157。说明原版声码器有较好输出上限，当前主要瓶颈是把输入者特征映射到目标特征。此控制不可拿来宣称实际转换达到0.77。

GRU映射器：20→64 tanh→GRU64→18，约2.7万权重；倒谱1–17残差受3std*tanh限制，音高残差±0.4，能量0及相关性19保留输入。实时仅部署这个小模型与声码器。权重格式FMAP006，C解析严格验证名称/长度/数值。

V1：1200步特征Huber+音高+时间差损失，48训练音频与4段真实目标锚点；没有波形感知、ASR/身份梯度。V2：先用过去200活跃帧归一化源倒谱，2000步；音色指标略升但字音变差。V2频谱历史未在静音后清空，这一点未被悄悄修复，现版本合同应保留原样，改动必须新版本重新训练。直接CMN控制较清晰但身份仍主要是输入者，都没有上板。

随后使用冻结PyTorch FARGAN将小映射器输出变成声音，加入多分辨率频谱、中文CTC、目标身份损失。中文和身份大网络只用于电脑训练，不部署7020。冻结原版权重没改；原版eval也会随机加激活噪声，训练代理显式改成确定性clamp。该代理不是量化C的逐位复现，波形NRMSE约1.4–1.5，相位递归差很大；最终评价必须用实际量化C重新合成。

训练代理160帧1.6秒：梯度有限，最大GPU占用约498MB；加入CTC/身份训练约1.55GB。全长递归梯度有少数过大更新，另实现每8帧/80ms截断反向传播（保留递归状态的数值，不重置前向声音）。新旧前向最大差0.0，梯度有限非零。截断仅影响训练，不改变板端声码器。

自然度/身份等分数不能替代听感。识别器、WeSpeaker加入训练损失后不再是独立评审；低编辑数、高余弦均不能单独给最终验收。UTMOS未用于梯度，但中文域未经验证。验证集多次用于开发调参，不是盲测。

## 数据边界

用户5段目标Track5–9，共121.98秒，48k/24bit/双声道，单人安静讲话、本人未变速变声；Track5–8约99秒用于训练，Track9约22.84秒未训练。公共AISHELL3：12个训练人物48文件，2个验证人物8文件，2个测试人物8文件；测试本轮未使用。
teacher来自CV3直接source-VC，不是识别后文本重读，没做整句时间拉伸、没做未来oracle波形混合。训练的源和教师尾部仅按既有≤100ms差裁/补。特征manifest在 `board_budget_20261005/fargan_corpus/manifest.json`。

固定中文输入保持“我的校园很美，走近大门就能看见宽阔的操场。”普通男声B文件仍在10月4日原台词文件夹，4.32秒、69120样本；未来试听要分别提供原声/教师/实际候选，不能换台词或拼在一条音频里。

## 最新开发验证指标（实际量化C输出；已有wide/DSP例外按原报告）

'''+ '\n'.join(table)+'''

缺指标表示尚未跑完检查，不表示分数为零。不合格候选不得偷偷替换当前用户认可基线。fargan_teacher_reconstruction是上限控制，其余FARGAN为实际源特征处理候选。

## 文件与复现

项目根：`D:\\Tools_FPGA\\workspace\\voice_conversion_zynq7020`。

- neural_reference：本轮准备/训练/评估脚本；`differentiable_fargan_20261006.py`、`fargan_feature_mapper_20261006.py`、`train_fargan_perceptual_20261006.py`、`train_fargan_truncated_20261006.py`。
- board_support/native_llvc_20261005：C与头文件、host/ARM可执行文件、构建及串口日志、转运SHA证据。`fargan_mapper.h`、`fargan_mapper_probe.c`、`native_fargan_mapper.c`。
- board_budget_20261005：corpus、每候选checkpoint/weights/decision/音频/heldout_screening、phonetic_naturalness自然度、fargan_proxy_verification代理校验、fargan_mapper_c_verification映射校验、fargan_native_stream_verification链路校验。保留这个历史目录名，不代表本轮发生于10月5日。
- CPU脚本可以用D:\\Tools_codex\\python；GPU训练用neural_reference/rvc_env/Scripts/python.exe；汉字/拼音检查用cosyvoice_env/Scripts/python.exe。Python3.14全局版本与3.12虚拟环境不同。
- ARM GCC是VivadoSDK2018.3的arm-linux-gnueabihf-gcc，O3/Cortex-A9/NEON/hardfloat/static；原版FARGAN编译DDISABLE_DEBUG_FLOAT使用int8权重。host GCC是Vivado2018.3的MinGW6.2，AVX2/FMA。缓存/TMP全在D盘。
- 本机RTX4050Laptop6GB，系统提交内存曾紧张。大评估器/训练按顺序跑，别同时启多个CTC/UTMOS进程。串口不能多进程同时打开。

## 接续步骤

1. 先读最新training_status/decision，不要重复已经完成的训练。若有运行中的脚本，等其结束并看错误；不可因为存在checkpoint便说目标完成。
2. 实际int8 C生成验证输出，按相同8段验证运行自然度/无提示文字识别/身份诊断。目标是相似度提高，字音/自然度不退步；检查逐句，不能只看均值。
3. 候选通过后，对同一个固定中文B生成C输出及ARM输出，检查音量/爆音/静音、真实整链速度/截止期、内存、功耗温度；量化C与PyTorch代理不能互换。
4. 准备明确可回退的板端助手与watchdog，再切换真实麦克风实时链，只请求一次有价值试听，说明当前候选而非宣称完成。声学延迟实测需要另做；PS/PL硬件加速尚未完成。
5. 未通过则保留wide，继续修复具体瓶颈，不要求用户重复已接受原声；不要仅把失败改成另一个算法名字，也不要盲目拉高增益。
'''
append='''

## 后续本轮实际新增：V8与扩充语料

更稳定反向传播轮240步935.125秒：自然度1.520147、编辑20/152、余弦0.550184，仍不通过。保留原始源音高作为第21个输入的GRU64轮3000步：自然度1.538585、编辑23/152、余弦0.555596，仍不通过；FMAP007，native数学校验通过不等于音质通过。

控制实验明确定位：正确教师频谱保留源能量，MOS2.650786；再保留源相关性，MOS2.392928，编辑6/152、余弦0.720729。和真实小模型的1.5/20字左右差距说明主要问题在特征映射学习。控制使用oracle教师特征，不能当实时转换效果。

原来的4.24分钟/12训练人物扩展到19.04分钟/20训练人物：新增192条888.1035秒，8个新人物男女各4；原12训练人物补充更多句子。先前尝试选32新人物失败，剩余符合条件的未使用成年男性只有4人，因此在转换前固定为上述平衡方案，没有偷用此前55个诊断人物或现有验证/测试人物。选取只依据固定顺序/拼音覆盖，非转换结果。

`student_corpus_expanded/source_manifest.json`、`paired_manifest.json`记录下载校验和CV3直接VC教师，目标参考仍固定T6前8秒。新增192配对全部生成成功。`fargan_corpus_expanded/manifest.json`保留原验证集，不读取测试音频，目标Track9不训练。转换教师无ASR/TTS、无波形时间拉伸。

V8：21→128 tanh→两层GRU128→19输出头，203411参数，FMAP008。谱1–17为受限残差；输出音高直接围绕目标中心193.133Hz预测，第一帧即目标音高，不等待源音高统计稳定；同时学习相关性19，能量0保留输入。第21输入仍是源原始音高；其他输入含过去统计，源人物无需登记。

训练固定5000步81秒；成对Huber/音高/相关性/时间差，1000步后加入离线条件特征判别器及特征匹配。判别器只在电脑训练，不部署板子。没有ASR、说话人或UTMOS梯度；不混波形；目标100秒真实录音锚点和20人公共输入教师共同训练。

V8开发验证8句：自然度1.637187、编辑15/152、目标余弦0.571124。音色比wide提高，但字音未全面胜过wide7/152；不能称最终完成。

固定校园句单独比较（全部未给识别器提示词）：普通男声目标余弦0.074174；现有wide0.258269；V8 0.645273。三个输出的拼音识别序列完全一致。汉字均把“走近”写为同音“走进”，各1编辑；不可将其说成拼音错。该句是反复开发样例，非盲测，分数不替代真人听感。

V8 native host映射相对Torch：NRMSE1.23687e-7，最大差1.66893e-6。双线程完整PCM流程和分步native映射→FARGAN69120样本逐位一致；RMS0.039795、峰值0.327728、无削波；零输入32000样本RMS1.16956e-6、峰值一个S16最低位。host检查不等同于ARM或现场音质。

未训练随机稠密权重V8 ARM结构计时432帧：平均2.019073ms/10ms、最大2.275032ms。该随机模型只是算力/数学原型，未播放、未作为音色转换候选。训练后的完整双核链仍需按最终ARM报告确认。

`native_fargan_v8_pipeline.c`：CPU0负责特征分析+映射，CPU1负责原版量化FARGAN；显式绑核，最多两个待合成特征帧，不能无限缓存语音。输出仍S16单声道16k，经既有ALSA适配硬件S24双声道44.1k。没有新PL计算加速，没有电脑参与现场推理。

该程序状态中mean_compute_ms是两并行阶段平均耗时的最大值（吞吐瓶颈），serial_compute_sum_mean_ms是两阶段平均耗时之和。二者都不是声学延迟。离线文件整体wall_elapsed_ms还要小于音频时长，现场还要看capture/aplay日志、进度和underrun；不能只把两阶段数值相加或只看最大均值宣称完成。

候选权重SHA256：5cf0ca6dcff4d11c4c2a20c21708ba8952cd12de2886774ee53942898ec5cfad。
板端新程序native_fargan_v8_arm，选择权重fargan_mapper_v8_selected.f32。助手board_neural_fargan.sh，依旧同一/run/voice-neural-live目录、相同已验收混音器；修订后周期208/缓冲832，播放启动延迟39000us。不得从这些配置值直接推算实际端到端延迟。新增audio_affinity.py把采集/播放/保护进程固定CPU0，CPU1专供声码器；保护失败会保留日志。tar解包助手后必须chmod +x或用sh执行，避免文件模式644导致Permission denied。

fargan_live_watchdog.py：检查归属明确的进程PID/进度，均值>10ms或超时块>5%（1000帧后）、新增多次underrun则停止并恢复wide；85℃是保守试验阈值，触及则只停，不自动重启发热负载。异常理由保存到板目录fargan_last_watchdog_reason.json。停止时根据PID的cmdline确认归属，避免误杀。助手未修改启动文件、音乐按键启动脚本或SD镜像。

最终当前运行版本以 `native/fargan_v8_live_evidence.json` 和板端实时状态为准；若该文件尚不存在，说明本轮还没确认正式切换。最新试验缺少听感或字音验收时不得设置quality_accepted/project_completed。用户当前不需要重新验证原声。
'''
live_path=native/'fargan_v8_live_evidence.json'
append+='''

## 训练权重的实际ARM验证与现场启动修复

正式权重完整ARM文件链432帧、4.32秒输入、69120样本输出：特征分析+映射均值3.568969ms，声码器均值9.018553ms，两阶段串行和12.587522ms，并行最大阶段11.082433ms，仅1帧超过10ms；总墙钟4001.342956ms。输出RMS0.038983865、峰值0.2799072、无削波。短文件RTF约0.926，余量有限，不代表长时间稳定或声学延迟。

host与ARM自回归波形NRMSE0.777672，存在相位递归差异，不能声称逐位一致。实际ARM固定校园句识别拼音与普通男声/旧基线完全一致，目标余弦0.633210（旧基线0.258269），但这是开发句且非真人验收。证据：fargan_v8_fullchain_verification/arm_verification.json、same_text_screen.json；E_板端计算_同一句中文.wav为实际ARM输出。

首次现场V8启动保护发现capture失效并恢复wide。故障时旧保护未保存完整日志，根因未确定。后来独立160/640采集测试退出0，不能认定该缓冲不兼容。助手恢复已使用的208/832/39000并新增音频绑核、故障日志；解包文件权限问题已通过chmod修复。修复后现场80秒：8000帧、声码器均值8.940042ms、分析映射3.514267ms、107/8000帧超10ms（1.34%，无重复播放欠载日志），温度约68.16℃，进程命令确认native_fargan_v8_arm、权重SHA一致。后续时刻以末尾保存的快照为准。

本轮已请求用户直接念同一句中文和随意讲话，比较新版音色及自然度；反馈尚未到达时保持质量验收false，不能把日志无错误当音质合格。已认可的wide权重、启动脚本仍保留。恢复命令：cd /home/root/native_llvc_trial_20261005 && sh board_neural_wide192.sh start。停止命令：同目录sh board_neural_fargan.sh stop。无需重烧SD、无需管理员权限、无需重做接线或原声验收。

本轮传输主包1946275字节SHA d23560f95e4af4050059719d12a0454a55bb0b18c44993ac31cec9ff2c984121；修复助手包2627字节SHA 6c2d781287f9cc5fb142dc79e22e79dc71107c4488b56a9c361885bd98002957。传输脚本逐文件SHA校验并恢复115200波特率。现场快照脚本snapshot_fargan_v8_20261006.py保存真实进程命令/权重校验/实时状态/日志/温度，不记录用户麦克风声音文件。
'''
if live_path.exists():append+='\n最后保存的板端状态证据：\n\n```json\n'+live_path.read_text(encoding='utf-8')+'\n```\n'
if feedback_path.exists():
    append+='\n## 后续真人否决与回退（覆盖先前待验收状态）\n\n```json\n'+feedback_path.read_text(encoding='utf-8')+'\n```\n'
    append+='\n用户反馈“不像，而且声音不清晰，会颤”。V8现场音质验收失败，已经恢复wide192；旧基线只接受噪声和字音，不代表目标音色已达标。不得继续将V8现场效果表述为很像/通过/待试听。机器余弦只是嵌入向量相似，不是像目标人物的百分比，不能抵消真人否决。\n'
    audit_path=budget/'fargan_v8_rejection_audit/audit.json'
    if audit_path.exists():
        audit=json.loads(audit_path.read_text(encoding='utf-8'))
        append+='\n离线相邻浊音帧音高变化诊断：\n\n```json\n'+json.dumps(audit['aggregate'],ensure_ascii=False,indent=2)+'\n```\n'
        append+='\nV8的相邻浊音帧音高跳动比教师更大，与颤音可能有关；这是离线测试的线索，尚未证明现场颤音根因。原现场日志无错误也不能证明无算法失真。审计及固定三组音高/相关性消融保存fargan_v8_rejection_audit与fargan_v8_*；不直接上板，不再仅凭音色余弦请求试听。新候选至少需固定开发集内容不退步、抖动/自然度诊断、真实ARM预算及真人验收；开发集反复使用不能称独立盲测。\n'
dest.write_text(text+append,encoding='utf-8')
old=Path('D:/总进度/原声验收后_模型改进_2026-10-05.md');pointer='\n\n2026-10-06增量续接：见 [目标音色继续改进_2026-10-06.md](目标音色继续改进_2026-10-06.md)。用户已接受噪声减少和字音，目标音色仍在改进；候选是否部署须以新文件与板端实际状态为准。\n'
if old.exists():
    previous=old.read_text(encoding='utf-8')
    if '2026-10-06增量续接' not in previous:old.write_text(previous+pointer,encoding='utf-8')
print(str(dest))
