# GitHub参考初查

检查日期：2026-10-09。来源为公开仓库页面与所链接源码，属于初查。页面存在缓存或抓取失败，尚未锁定提交；复用前仍需取得明确提交、保存授权与依赖说明并运行测试。当前新增参考由本项目编写，未复制第三方源码。

## 优先参考：基础变调

[jmt329/PitchShifter](https://github.com/jmt329/PitchShifter) 面向DE1-SoC，采用循环缓冲时域变调。可研究读写相位和定点实现；板级HPS、Avalon、M10K与GUI不能直接用于Zynq/PYNQ。[MIT许可证](https://github.com/jmt329/PitchShifter/blob/master/LICENSE) 已查看。

[buffer.v](https://github.com/jmt329/PitchShifter/blob/master/buffer.v) 初查有两处疑点：默认B=1024时内部 `read_address_reg` 仅9位；第二个RAM的写地址连接 `rb1_write_addr`，而 `rb2_write_addr` 被单独维护。这可能导致地址截断和半缓冲偏移失效，须通过独立测试验证。接口也没有完整输出背压支持。以上为源码推断，尚非仿真定论。

处理决定：借鉴路线，先建立本项目流式参考；不直接包装该文件成AXI核。

## 备选算法

[FPGA Autotune](https://github.com/frequency-perfected-generated-audio/autotune) 的 [README](https://raw.githubusercontent.com/frequency-perfected-generated-audio/autotune/main/README.md) 描述YIN与PSOLA。其延迟是作者声明，本板未复测。许可证、模块接口和仿真尚未核实；不在当前旁路关键路径引入。

[Sprocket](https://github.com/k2kobayashi/sprocket) 的说明明确采用源/目标平行数据训练GMM或DIFFGMM。它可作为传统声线转换实验参考；不能据此承诺仅现场录目标即可泛化任意输入者。其依赖和板端运行成本未验证，不先安装到本机环境。

## 模块组织参考

[MongooseOrion/Audio_Time_Freq_Process_and_Trans](https://github.com/MongooseOrion/Audio_Time_Freq_Process_and_Trans) 使用PGL50H，仓库标示GPL-3.0；不是Zynq-7020现成工程。可参考音频模块组织及测试思路。README中的MFCC/VQ模块负责声纹识别，音调模块提供升降调，这两者组合不等于生成目标音色。DDR、UDP和HDMI不纳入首期移植。

VoicePrivacy、LLVC、RVC本次没有重新审计，继续保持为原规划中的后续研究或电脑音质对照项。
