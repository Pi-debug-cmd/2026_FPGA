# 7020原生小模型推理：2026-10-05部署准备进度

## 为什么做这个阶段

用户强调模型必须以可搭载7020为硬约束，不能先无限完善电脑大模型再考虑部署。
当前CosyVoice3只保留为离线教师/质量参照；它不是已交付板载模型。
本阶段把已有目标20步LLVC检查点的完整推理移植为ARMv7原生程序，先取得真实模型在板端计算的基线，再约束后续质量/速度/内存。

## 现在确实完成了什么

1. 从严格加载的checkpoint_step20.pt导出148个张量，学习权重、位置编码缓冲与预计算零label条件均保留。
2. 导出模型llvc_step20.f32为13,250,059字节；不是CV3，也没有新训练。
3. 编写native_llvc.cpp，完整实现固定LLVC几何：
   12层带缓存filter/gate残差前端；48tap/stride16输入卷积；
   8层深度卷积+LayerNorm+点卷积残差编码器；
   grouped512/256投影；8头self/cross attention；
   feedforward与3个LayerNorm；label整合；
   80tap/stride16输出转置卷积和tanh；
   encoder/decoder/output/prenet状态及16样本有限前看、32样本前侧历史。
4. 原生电脑标量版与未改PyTorch流式参考做静音、纯音、真实中文、209样本跨块边界对照，长度一致、输出有限。
   最大NRMSE约2.62e-5；最大绝对误差约2.04e-8。
5. 模拟ARM NEON四路累加顺序的电脑测试通过，相同四项最大NRMSE约1.24e-5；最大绝对误差约1.77e-8。
   这是计算顺序模拟，不能冒充实际ARM执行。
6. EOF长度0/1/16/207/208/224/416正确，拒绝非有限输入。
7. 编译native_llvc_arm，1,846,796字节，ARMv7/Cortex-A9/NEON/hard-float，静态链接，避免依赖板上Torch/Python包或不兼容libstdc++。
   readelf确认ELF32 little endian ARM EABI5、NEON/VFP属性。
8. 导出manifest、源/模型/程序SHA与数值验证JSON。

完整文件式推理命令（先传入板上专用目录并核对SHA才运行）：
    ./native_llvc_arm ./llvc_step20.f32 ./real_16000.input.f32 ./real_16000.arm.f32

输入与输出为little endian float32、16kHz单声道原始采样，输入限30秒；不是WAV头文件。
正式首次ARM运行应使用416样本短控制，再核对PyTorch参考；通过后测试1秒真实源，观察速度和输出。
程序输出samples/chunks/inference_seconds/mean_chunk_ms/max_chunk_ms/peak_rss_kib等JSON。
首次原生程序是文件式试验，不直接连接无限麦克风流；内部块处理和缓存合同一致，不等于完整实时IO已经做好。

## 边界与尚未完成

- 当前板卡没有得到shell。COM8是CH340已枚举，但上次6秒串口探测无root响应。
- 尚未传入板卡，尚未实际ARM执行，NEON实际误差/性能/峰值内存必须上板再核对。
- 不把ELF头检查成功当作板上可执行成功。
- 不把电脑标量速度用于宣称ARM速度。电脑该原生实现1秒音频约2秒处理，移植目标首先是完整正确；没有证明实时。
- 单线程纯PS很可能慢。原先8个点层234ms/13ms的板上合成基准也显示风险，后续须实测并加速/缩模型。
- 20步模型只训练2句话，音色/发音已知未通过。移植它是取得板端运行基线，不是改口称它合格，也不代表教师C的效果。
- 没有加载自研PL加速核；核心本阶段先在板上PS计算。PL仍是官方音频硬件。
- 没有改SD、bitstream、旧voice_stream、开机服务或目标原件。
- PCM44.1k/24bit双声道与16k float单声道的完整现场格式桥、真实录音和WAV播放仍待准备/设备确认。
- 原生包可放独立目录回退到voice-live.sh start bypass；初次不替换开机入口。

## 后续硬约束

最终验收仍是任意未登记人输入、同一目标人物、7020核心计算、自然正确中文、持续低延迟。
部署评审要同时列实际内存峰值、每13ms块处理/最坏耗时、全系统吞吐与音质，不把“小文件能复制进去”当作实时完成。
先拿到ARM完整基线，再按预算做学生结构/定点量化/PL热点，已验证128矩阵核可以作为候选，但完整音频2022.2集成仍未解决。
大教师的认可②、最新待听C，以及旧③人工失败登记继续保留。当前工作不洗白失败音频、不新扫教师后处理。

## 产物

export_model.py / model_manifest.json / llvc_step20.f32
native_llvc.cpp / native_llvc_arm
native_llvc_host.exe / native_llvc_neon_order_host.exe
verify_native.py / native_numerical_verification.json
verify_neon_order.py / native_neon_order_verification.json
numerical_tests.json / deployment_artifacts.json
各*.input.f32、*.torch.f32、*.native.f32、*.neon_order.f32是精确数值测试。
fleurs_full.input.f32是既有公开真人源，不是用户目标人物输入。

## 下一次需要用户提供的信息

请确认板卡已上电、SD在板上、USB插在串口口，麦克风粉口与音箱绿口接好；COM号可能变化。
先获得shell只读查询内存/存储/音频/网络。再决定安全传文件方式（有线网络较快，115200串口传13MB权重需较久），不额外重烧SD。