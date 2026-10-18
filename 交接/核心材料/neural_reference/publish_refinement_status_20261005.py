from pathlib import Path
import json,datetime
BASE=Path(__file__).resolve().parent;budget=BASE.parent/'board_budget_20261005';native=BASE.parent/'board_support/native_llvc_20261005'
def read(p):return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None
live=read(native/'wide_live_trial_evidence.json')
evidence=dict(time=datetime.datetime.now().isoformat(),board_mode='accepted original passthrough, no neural inference or mic dump',accepted_mixer=dict(Capture=43,Headphone=119,Playback=222),original_feedback_accepted=True,repeat_original_verification_required=False,
 vector128=read(native/'small128_vattn_board_check.json'),wide192=read(native/'wide192_outpack_board_check.json'),pcm_contract=read(native/'small128_pcm_contract_verified.json'),bulk_stream=read(native/'updated_student_bulk_stream_audit.json'),
 reconstruction128=read(budget/'phonetic_naturalness/small128_reconstruction.json'),target128_400=read(budget/'phonetic_naturalness/small128_target_anchor_step400.json'),target128_800=read(budget/'phonetic_naturalness/small128_target_anchor_step800.json'),target128_1200=read(budget/'phonetic_naturalness/small128_target_anchor_step1200.json'),target128_1200_asr=read(budget/'small128_target_anchor_step1200/heldout_screening.json'),
 training128_interruption=read(budget/'small128_target_anchor/interruption.json'),full512_control=read(budget/'phonetic_naturalness/full512_official.json'),full512_targetpilot_control=read(budget/'phonetic_naturalness/full512_targetpilot.json'),hybrid=read(budget/'neural_band_hybrid/report.json'),hybrid_identity=read(budget/'neural_band_hybrid/small128_target_anchor_step400_cut1200/heldout_screening.json'),
 wide_reconstruction=read(budget/'wide192_shallow2_reconstruction/decision.json'),wide_reconstruction_refined=read(budget/'wide192_shallow2_reconstruction_refined/decision.json'),wide_reconstruction_refined_naturalness=read(budget/'phonetic_naturalness/wide192_shallow2_reconstruction_refined.json'),teacher_timing=read(budget/'teacher_content_timing/report.json'),wide_conversion=read(budget/'wide192_shallow2_target_anchor/decision.json'),project_complete=False,quality_accepted=False,pl_acceleration_added=False)
if live:
 evidence['board_mode']=live['board_mode'];evidence['wide_live_trial']=live
(native/'continued_refinement_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
text='''# 原声验收后的模型改进与续接记录（2026-10-05）

本文件只记工程。总目标仍是任意现场讲话者通过麦克风输入，在野火Zynq7020上低延迟变成预先采集的目标人物声音。不是单纯升降音调，不需要提前登记输入者，也不能以原声直通、预先录音等待转换或电脑推理代替最终成果。项目尚未完成。

## 当前板子状态与用户已通过的验收

用户最后明确确认：原声实时播放清晰、音量够、没有过多杂音。采集43（+15dB）、耳机119（-2dB）、播放222（-16.5dB），ADC PCM190、LINPUT1 boost1。这个反馈足以验收当前原声链路。不要继续要求用户证明麦克风接线、音箱电源或重复录音来验收原声。当前板子仍是pcm_bridge_bypass原声；没有转换模型，没有麦克风诊断录音。最近原声进程26078/26079/26080，需继续工作时读实时进程确认。

新文件都保存在D盘。没有重烧SD卡、改启动、改物理磁盘或装驱动。COM8，root/root，115200；独占串口，上一条串口工具必须结束后才发送下一条。大文件工具uart_transfer.py使用230400，完整SHA256确认后恢复115200。原声回退脚本已上传：/home/root/native_llvc_trial_20261005/board_original_accepted.sh，自动恢复上述已验收音量。新运行程序上传仅用于文件运算，不代表切换到现场转换。

## 已完成的运行程序改进

对原来FP32程序的LayerNorm、exp/tanh/sigmoid和注意力加权部分使用NEON计算；近似函数先与标准函数核对，再与PyTorch实际网络逐样本比对。E128/D64的板上输出归一化误差约1.09e-6；公开10.38秒输入的平均块计算12.1009ms，最大16.1425ms。13ms为音频块节拍。PCM流式文件输入16000和209样本，与电脑参考int16输出完全一致；没有采集用户麦克风。

之后对输出卷积重新排列不可变权重，并把同一组4个输出样本的累加保存在NEON寄存器，减少反复读写输出缓冲区。新结构E192/D96、2个DCC编码层、8个注意力头、1个解码层、13帧块、L16、208样本块；315968参数。编码器历史为6帧/96样本，另有注意力缓存与前置卷积历史；不能把旧8层编码器的历史长度套到新模型上。输出基底和解码通道比E128/D64各增50%，但编码层从8减少到2。这是重新设计的候选结构，不是声称剪裁后保持质量。

新结构在实际7020上跑公开10.38秒文件：平均11.3872ms/块，最大17.0617ms，RSS4864KiB。与PyTorch参考误差5.57e-7；1秒另一个文件误差9.31e-7。平均速度足以继续候选训练，但还不是麦克风实测、没有声学延迟测量、没有音质验收。所有推理仍在PS双核ARM；本轮没有新PL加速器。

源码、程序与证据：
- board_support/native_llvc_20261005/native_llvc_small128_vattn.cpp与_meter版本。
- native_llvc_wide192_shallow2_outpack.cpp及_arm程序。
- prepare_wide_shallow_geometry.py：构造192通道、2层结构；导出wide192_shallow2_initial.f32，仅初始化。
- small128_vattn_board_check.json、small128_pcm_contract_verified.json、wide192_outpack_board_check.json。

## 已实际训练但不接受的128通道试验

首先做800步原声重建预训练，使用已有12位训练说话人的48段公开语音以及目标人物Track5–8，始终不使用Track9。损失是准确波形L1与多分辨率声谱，意图修复剪裁后的小波形编码/解码器。这仅是预训练，不是把原声还原叫作目标人物转换。公开验证的字错9/152，原声5/152；自然度预测1.31264，明显不足。

再从这个重建检查点开始训练目标转换：两段公开训练源/对应CV3直接转换教师、1段目标人物原声重建约束、1段非语音；声谱、拼音CTC、说话人嵌入、对抗和特征匹配、安静输出损失。原目标是2400步；保存400/800/1200步检查点，因电脑提交内存不足导致评估加载失败，实际在最后一次日志1281步之后结束该试验，最后可复现保存是1200步。不要称2400步训练已完成，见interruption.json。

128通道转换的独立UTMOS自然度预测：400步1.26557、800步1.26662、1200步1.27077；原先6400/9200小模型1.23460/1.23292，公开源2.44522、CV3教师3.56968。这点变化不构成自然度验收。400步中文字错11/152，1200步12/152，1200步目标嵌入余弦0.35895。虽然比旧小模型保字好，目标音色仍不足。没有部署这些试验到麦克风音箱。

拼音与汉字评估共享已经作为训练损失的SenseVoice编码器，说话人网络也参与训练，所以不能称它们独立或把得分当真人认同。UTMOS没有参与训练，但中文域没有标定，也不能代替试听、发音或音色判断。现有公开验证已反复用于开发，不能再宣传为全新盲测。

## 拒绝的高频原声保留方案

另做63抽头Blackman互补FIR试验：低频由转换网络生成，高频保留公开源录音。这个混合必须明确披露，不能标成纯神经转换或最终目标人物声音。低通1200/2200/3200Hz，额外群延迟31样本/1.9375ms，不离线对齐，不使用未来音频。

128/400步+1200Hz方案的自然度预测提高到2.00982，字错4/152；但目标音色嵌入仅0.18230，与原声0.18925类似，说明保住清晰度的同时仍主要保留输入者声音。用户要求的是指定目标人物，因此这个方案拒绝，不上传转换音箱、不当成项目进步。9200旧网络同样融合也只有约1.27自然度。

## 完整宽度对照与新结构方向

相同公开验证下，完整512通道官方检查点自然度预测2.03328；完整512通道20步目标试验2.00878。这不是目标人物验收，也没有板上实时跑完整模型。与当前剪裁小模型的差距支持关注模型容量和声音重建能力，但不能证明剪裁是唯一根因。已有“mask=1”检查连完整模型也不能还原原声，不能用它单独论证编码器坏了。

本轮随后采用E192/D96、2层的宽而浅结构，在13ms处理预算内扩大重建与解码通道。先完成800步重建，再单独在wide192_shallow2_reconstruction_refined从800检查点继续2400步，累计3200步；续训中准确波形损失由8增至24，学习率降至1e-4。流式公开验证自然度预测由1.38341升至1.87206，这是原声重建能力改善而不是目标声音验收。新3200检查点的bulk/stream在两段语音的归一化差约5.77e-6/3.11e-6，没有支持前置卷积缓存差异导致本轮明显失真的证据，因此没有修改已验证的流式契约。

另外核对48段训练源与CV3教师的HuBERT前9层特征，受限DTW只用于诊断、不修改音频，也不加入训练：活动段平均绝对时间偏移约0.485ms，未支持明显发音错位为主要问题。诊断不等于真实音素标注，feature时长相符也不意味着声音已验收。代码audit_teacher_content_timing_20261005.py，结果board_budget_20261005/teacher_content_timing/report.json。

接着从3200步重建检查点开始800步目标转换固定长度试验。转换仍使用原48段训练源及对应教师，Track5–8自重建约束，Track9不训练。中文CTC每4步使用一次；对抗鉴别器输入分别归一到RMS0.1，避免低音量使小鉴别器难以区分；身份损失权重3、目标自重建波形损失2，完整损失见train_board_wide_shallow_target_anchor_20261005.py。所有重型辅助模型只在电脑训练，板上只运行小网络。具体完成状态应读decision.json和实时进程，文件存在与上传不代表训练或上板完成。

该800步转换试验已实际完成：独立自然度预测1.61297，相比旧9200步1.23292有进步；同一8段公开验证汉字错7/152，旧6400/9200步22/27；目标嵌入平均余弦0.50057、源0.18925、CV3教师0.87253。识别器与说话人网络用于训练，分数不能当独立验收。基于综合开发结果，选择进行现场清晰度/杂音试验，不能宣称目标音色已经完成。

更具体的音高检查发现一个明确缺口：公开男声输入的基频中位约124–144Hz，教师转换约200–217Hz，新小模型输出仍约125–144Hz。女性输入也大致保留输入基频。这支持后续显式处理目标音高/有声激励与音色生成的方向，而不是认为当前已能把任何输入者完整变成目标人物。Praat自相关只是信号估计、不等于听感验收；不得把音高差当音色唯一差异，也不能跳过后续模型与算法数值和板上速度验证。结果wide192_shallow2_target_anchor/pitch_profiles.json。下一阶段可以评估因果音高控制、连续相位激励或训练一致的音高预处理；目前未实现这些。

## 下一步与操作边界

先读最后的continued_refinement_evidence.json及本文件，检查新结构是否训练完成；用未参与训练的公开验证语音进行流式导出，再依次做自然度与内容诊断，避免同时加载两个大评估器导致电脑内存不足。计算检查不等于音质改善，ASR不等于发音验收。若新结构确有值得试听的进步，先导出正确权重、SHA校验、板上文件数值和速度检查，再保持已验收音量进行实际实时试听。当前原声反馈不需要重新验收。

试听对照须保持同一句中文和分开的文件。固定句子“我的校园很美，走近大门就能看见宽阔的操场。”已有A目标原声、B普通男声输入、C转换；B是Kokoro合成男声而不是真人。不要混入目标原声，不换文案、不强行时间拉伸，不给源说话者登记参数。若新结构仍失真，不重复提高音量或把原声混进去冒充目标音色；应继续检查模型表达能力、教师训练对齐与更充分的训练数据，并评估更大模型所需PL加速。

详细旧工程交接：D:/总进度/7020实时小模型工程续接_2026-10-05.md。基础目录D:/Tools_FPGA/workspace/voice_conversion_zynq7020。可执行脚本在neural_reference，部署与UART工具在board_support/native_llvc_20261005，所有新训练在board_budget_20261005独立目录。用户授权继续推进，只在需要真实帮助或值得试听时请求协助。
'''
dest=Path('D:/总进度/原声验收后_模型改进_2026-10-05.md');dest.write_text(text,encoding='utf-8')
print('SAVED',str(dest),flush=True)
