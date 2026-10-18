# 本轮基础变调开发与验证

日期：2026-10-09。保持原项目单目标注册/音色研发范围；本轮构建可控基础变调参考与RTL，未宣称目标音色完成。

## 完成物与复现

| 完成物 | 入口 | 证据 |
| --- | --- | --- |
| 根目录查阅指引 | `project_guide.md` | 当前决策、短查阅顺序、板端版本与接续点 |
| 整数参考 | `src/reference/pitch_shift_fixed.py` | 与同量化比例浮点参考误差<3 LSB；跨块/复位一致 |
| 定点契约 | `team_project/fixed_point_contract.md` | 位宽、舍入、相位、缓冲、握手与复位定义 |
| 变调RTL+RAM | `src/rtl/axis_pitch_shift.v`、`pcm_delay_ram.v` | 6档共24576黄金样本逐项一致，背压/TLAST/回绕/复位通过 |
| 注册/校准参考 | `src/reference/voice_profile.py` | 文件注册、基频统计、静音/削波/有效时长拒绝，异常不覆盖旧档案 |
| 24位录音处理 | `src/reference/audio_io.py` | PCM24解码、通道选择、127抽头FIR整数降采样测试 |
| Python自动测试 | `python -m unittest discover -s sim -v` | 17项通过，`reference_tests.txt` |
| Vivado仿真 | `build/run_pitch_sim.ps1` | `pitch_sim.txt` |
| 独立综合 | `build/synth_pitch.tcl` | `pitch_utilization.txt`、`pitch_synth_timing.txt` |
| PS C参考 | `src/ps/pitch_fixed.c`、`build/build_ps_reference.ps1` | SDK 2018.3交叉编译，-Wall/-Wextra/-Werror通过 |
| ARM数值验证 | `python -m sim.generate_ps_vectors`、`python -m sim.verify_ps_board_log` | COM14实测，12种格式/比例组合SHA相符 |

完整模块没有AXI-Lite控制寄存器、PS/DMA工程或新的板级bitstream，综合报告是独立模块结果。

## 资源问题与修复

首版缓存写法未推断成BRAM：2035 LUT（其中1408 LUTRAM）、178寄存器、0 BRAM、6 DSP。简单合并写口虽减少了一半LUTRAM，仍没有解决BRAM推断。初期乘加链也曾出现100MHz综合估计WNS=-1.423ns。

修复：统一RAM写地址/数据、隔离同步双口RAM模块并保留层级，避免综合在多处样本消费中展开读结构；给插值/淡化乘法和求和增加流水级。每次行为修改都重新核验24576样本。

最终独立综合：**340 LUT、117寄存器、1块RAMB36、6 DSP**；-1器件、10ns时钟下综合估计WNS=+4.311ns、TNS=0、WHS=+0.252ns、THS=0。没有布局布线，OOC时钟源未指定且I/O延迟未定义，所以不能当完整板级时序通过或最高频率实测。上16位输入按接口契约不用，综合有未连接警告，非样本丢失。

## 目标录音与试听样本

运行 `python -m build.run_reference_demo` 可重建 `data/reference_demo/`：

- 原始目标Track5：48kHz双声道PCM24，选择第0声道；127抽头中心FIR降采样到16kHz，属于离线操作，不作为实时重采样实现。
- 输出目标F0中位数193.8308Hz，源开发样本中位数146.2516Hz，固定比例1.325324（Q16=86856）。有效覆盖、RMS和SHA在档案中。
- 源为交接已有开发说话人SSB0434的四段语音，总输出22.73775秒。不是新的独立测试集。
- `target_reference.wav`、`source_original.wav`、`pitch_only.wav`分别为目标、原声和仅变调；没有混音，未做目标音色增强。记录 `demo.json`。

当前注册仅生成F0校准档案，不包含人物身份/音色模型。YIN范围75～400Hz、40ms窗/10ms步长、阈值0.15、有效有声窗覆盖至少3秒、削波不超过1%均为首版工程规则，需真实多人语音验证。不能凭合成正弦通过就认定这些阈值泛化可靠。

## 当前停止点

已确认COM14与厂商音频设备，板端PS数值通过。已准备有限20秒实流脚本且语法检查通过；因需要用户讲话/听辨，当前尚未启动。后续先验证原声旁路，再验证基础变调听感，保存xrun与实际参数，然后接完整PL工程。不能拿PS-only试听代替PL上板。
