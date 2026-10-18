from pathlib import Path
import json,datetime
base=Path(__file__).resolve().parent;project=base.parent;budget=project/'board_budget_20261005';native=project/'board_support/native_llvc_20261005'
records=[]
for name in ('fargan_v8_dynamics','fargan_context_v9'):
    folder=budget/name;r=dict(name=name,quality_accepted=False,board_live_deployed=False)
    for file,key in [('decision.json','training_decision'),('development_gate.json','development_gate'),('pitch_dynamics_audit.json','dynamics_audit'),('native_verification/verification.json','native_host_verification')]:
        path=folder/file
        if path.exists():
            d=json.loads(path.read_text(encoding='utf-8'))
            if key=='training_decision':d={k:d[k] for k in ('complete','steps','parameters','mapper_sha256','parent_sha256','source_enrollment','raw_waveform_mix','recognizer_used_as_loss','test_audio_used','target_track9_used','training_frames','warmup_frames') if k in d}
            if key=='dynamics_audit':d=d['aggregate']
            r[key]=d
    if 'training_decision' not in r and (folder/'training_status.json').exists():
        d=json.loads((folder/'training_status.json').read_text(encoding='utf-8'));r['last_training_progress']=d['history'][-1]
    records.append(r)
guides=[]
for name in ('fargan_phone_guidance','fargan_phone_ctc','fargan_phone_cmn'):
    q=json.loads((budget/name/'qualification.json').read_text(encoding='utf-8'))
    guides.append(dict(name=name,summary=q['summary'],gate_passed=q['diagnostic_gate_passed'],used_for_conversion_training=False,board_deployed=False))
diagnostic={}
p=native/'wide_diagnostic_verification_20261006/verification.json'
if p.exists():diagnostic=json.loads(p.read_text(encoding='utf-8'))
report=dict(updated=datetime.datetime.now().isoformat(),user_instruction='一直执行，只有需要协助、值得试听或遇到无法独立解决的问题才停',
            accepted_baseline='wide192_shallow2_target_anchor',original_route_accepted=True,
            rejected_live_v8_feedback='不像，而且声音不清晰，会颤',project_completed=False,
            new_candidate_live_deployed=False,target_identity_accepted=False,candidates=records,phonetic_guides=guides,wide_ram_diagnostic_verification=diagnostic)
(native/'continuous_refinement_evidence_20261006.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
text='''# 持续修复工程续接：2026-10-06

本文件承接“目标音色继续改进_2026-10-06.md”，只记录工程。目标仍是任意未登记讲话者实时转为固定目标人物，在野火7020主要运行，中文清晰、自然、低延迟。PS模型与官方PL音频链不是自研PL模型加速。原声通路已验收，不重复要求用户验证；wide基线只接受杂音/咬字，目标音色未通过。用户否决现场FMAP008 V8“不像、不清晰、会颤”，已回退，状态证据有独立历史与当前快照。

用户再次明确要求持续执行。不得仅解释后结束，遇失败继续独立修复；只在确需操作、有价值的新试听或实质外部阻碍时等待用户。不得以新增一次分数上升包装完成，也不得反复请用户听已知字音退步版本。

第一轮：fargan_v8_dynamics。保持21输入、128两层GRU、19输出、FMAP008与原生架构，从原V8 checkpoint_step5000细调4000步（63.344秒）。训练240输入、20训练人物、19.04分钟，目标Track5–8锚点；Track9/测试音频不使用。去掉该控制中的特征判别器，不用ASR/声纹/UTMOS梯度。新损失约束倒谱变化、连续浊音帧音高的一阶/二阶变化、相关性变化；片段400帧/4秒，前16帧暖机，短片段显式mask右侧静音补齐，谱和能量增益增强保留。所有现场处理仍因果，无原声/目标波形混合。

结果：音高相邻帧平均变化由旧V8约0.3469半音降至0.2077，教师约0.2073；大于2半音跳变由8降0。只是离线特征诊断，不能宣称现场颤音已修复。8句内容16/152，比wide7/152退步；自然度预测1.8493、余弦0.6110，均非听感验收。因此未上板。Native host数学NRMSE约1.075e-7、最大2.265e-6；固定原校园B为4.32秒69120样本、无削波，零输入RMS3.412e-7。数学正确不意味着音质合格。

第二轮：fargan_context_v9，FMAP009。输入为原21特征，加过去最多200个活跃帧的17倒谱均值及计数置信度，共39输入；128两层GRU不变，约增加2304预处理层权重。统计只使用当前和以前帧；静音超过80个条件帧后清空，按环保存，不能用整句均值。自动统计不是要求输入者登记/录参考音频，不要求先等2秒再说话，不引入未来窗口。过去上下文的长度也不等于端到端声学延迟。

V9初始化从动态修正版继承21输入权重、新18输入权重置0，新增均值方差仅来自训练语料；固定10000步后才开发集评估，没有看测试集选checkpoint。继续动态损失。学习目的：让模型区分源音色/通道与音素细节，减少内容与音色混淆；该假设须以实际检查证明，不能提前说成功。

Python fargan_mapper_context_20261006.py；训练train_fargan_context_20261006.py由prepare_context_training_20261006.py生成（不要重复覆盖已训练产物）。Native fargan_mapper_context.h/probe_context.c/native_fargan_context_pipeline.c由prepare_native_fargan_context_20261006.py生成；build_native_fargan_context_20261006.ps1静态构建host/ARM，保留旧版不覆盖。FMAP009加载器必须拒绝旧FMAP008；双核合成/映射仍分线程，最多2个待合成特征帧。工具版本2018.3 ARM GCC与FPGA工程版本不是同一问题；官方Vivado工程2022.2、本机已确认2018.3，后续PL开发需处理兼容，未改现有bitstream。

验证顺序：训练完成 → evaluate_fargan_dynamics_20261006.py --candidate fargan_context_v9（固定8句无提示ASR/声纹+UTMOS诊断）→ audit_fargan_candidate_dynamics_20261006.py --candidate fargan_context_v9 → verify_fargan_context_native_20261006.py（新的39输入C数学/零输入/固定原B验证）→ 通过开发门槛再做真实ARM整链预算和小范围现场试听。不要把机器余弦解读为相似百分比。开发集重复使用不是盲测；最终需独立讲话者、真实麦克风域、实测声学延迟、温度长时及真正PS/PL加速集成。

当前运行与反馈以board_support/native_llvc_20261005中的证据文件及板端/proc命令为准；无合格新候选时保留wide。串口COM8 115200，独占；所有工程/缓存D盘。不改SD分区、开机镜像、官方bitstream。记录如下（缺项表示尚未验证）：

'''
text+='''第三轮完成情况：V9固定10000步169.484秒。开发集18/152、自然度预测1.8325、声纹余弦0.6090；同样未通过。相邻浊音音高变化0.2043半音、大跳变0，仅为离线诊断。新的C输入/映射NRMSE1.214e-7、最大1.669e-6，固定B零削波，零输入输出为0。ARM程序已静态编译，但因为内容退步而没有上传部署或声称实板预算通过。

随后准备了离线训练辅助的拼音内容指导器，目的是从20维合成特征监督中文字音。244段训练来源（240公共训练输入、目标Track5–8），用无提示的原始输入ASR产生1191拼音token后去掉声调合并404类；教师特征共享原输入标签，不用开发/测试音频产生训练标签。第一版17倒谱块+双向GRU逐帧后验3000步训练正例准确率约99.5%，但8句开发拼音序列错率原声127/152、教师85/152，说明该辅助器不能泛化。第二版20维CTC不要求峰位置对齐、固定10000步，开发99/152与65/152。第三版加入活跃片段均值去通道（只在离线辅助器，非部署流程），固定10000步91.109秒，开发104/152与74/152。后三版均未达到预设原声及教师序列错率<=0.25的门槛；不能用于转换模型损失、验收或给用户证明读音正确。双向/整段均值仅是被否决的训练辅助设想，没有引入现场未来帧。不是三版新的可部署转换模型，也不是三次有效改进。大量训练记忆与开发失败的差距是证据；具体根因仍须区分数据、特征、架构与麦克风域，不能直接下结论“用户素材不足”。

现场诊断准备：旧actual_mic_diagnostic_20261005a/input.wav全为PCM -1，不能当有效讲话。新native_llvc_wide192_diag120.cpp只对已经使用的wide192基线加入120秒输入/输出RAM环，模型、权重、混音/增益和运算不变，播放期间没有SD保存。收到说完反馈后board_neural_wide_diag120.sh finish先停采集/看门狗，让模型排空到EOF，才保存mic_wide_diagnostic_20261006.input.s16/.output.s16/.json，然后恢复board_neural_wide192.sh基线。COM8独占，不并行。既不是登记输入者，也不是先录后播的最终模式。采样用于真实声音离线复现诊断；需要用户说固定校园文本两遍并回复说完，其他线缆/开关不需变更。保存位置板端/home/root/native_llvc_trial_20261005，最终取回D盘并校验SHA。尚未收到有效现场讲话时不能声称诊断完成。

verify_wide_diagnostic_20261006.py通过0、1、207、224、16000、69120样本的S16输出逐字节与同参数编译的原程序完全一致，截获输入/输出完全一致；另外直接测试120秒RAM环跨界，并保留16样本lookahead，时间索引完全一致。仅验证数学/采样代码；实际ARM持续性能、声音是否真有讲话需要现场证据。该诊断不需要烧SD卡、改PL或改变开机脚本。

'''
text+='```json\n'+json.dumps(report,ensure_ascii=False,indent=2)+'\n```\n'
dest=Path('D:/总进度/持续修复工程_2026-10-06.md');dest.write_text(text,encoding='utf-8')
older=Path('D:/总进度/目标音色继续改进_2026-10-06.md');old=older.read_text(encoding='utf-8')
pointer='\n\n后续持续训练与新增39输入版本：见 [持续修复工程_2026-10-06.md](持续修复工程_2026-10-06.md)。以新文件和实际状态为准；候选未验收不能宣称项目完成。\n'
if '后续持续训练与新增39输入版本' not in old:older.write_text(old+pointer,encoding='utf-8')
print(json.dumps(dict(path=str(dest),candidates=[r['name'] for r in records]),ensure_ascii=True))
