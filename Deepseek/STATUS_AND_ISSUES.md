# 当前状态与已知问题（交接必读）

更新时间：2026-10-27

## 一、已经确定成立的

1. **转换算法正确**：板上输出与电脑端 Python 参考逐样本一致
   - corr 0.99999999、SNR 75.71 dB、max 4 LSB（4 s 音频，O64 模型）
   - 23.72 s 整段：identity 0.7324 / UTMOS 2.1532 / P10 0.6903 / leakage_rel −0.0343
2. **实时链路**：300 ms 块，cum_rtf ≈ 0.78–0.86，30 min 连续 6000/6000 块、aplay 报 0 欠载
3. **PL 参与计算**：STFT/IFFT + 频域增益在 PL 内，16723 LUT / 22 BRAM / 76 DSP，WNS +0.347，端到端 corr 0.99999999
4. **板级可执行文件**：`/tmp/vc/vc_pl_dbg3` + `student_v5_o64.blob`（64 阶）

## 二、没有解决的（必须知道）

### 1. 模拟输出（喇叭/耳机）出声不正确 —— 最高优先级
- 现象：aplay 正常执行、无报错、RTF 正常，但喇叭里全是噪声/沙沙声
- 直接播放未经转换的原始 PCM（`aplay -D default -t raw -f S24_LE -r 32000 -c 2 in.raw`）同样是噪声 → 与转换算法无关
- 每次打开音频设备，内核都打印：
  `wm8960 0-001a: slave mode, but proceeding with no clock configuration`
- 判断：WM8960 编解码器的时钟（MCLK/BCLK）未被正确配置，DAC 工作异常
- 排查过的：硬件协商格式固定 `S24_LE / 32000 / 2ch`（与程序输出一致）；`Playback`/`Speaker`/`Headphone` 均 100%；`Left/Right Output Mixer PCM` 已置 on
- **未做**：设备树里 WM8960 的 clock 配置修改（需要重新生成 dtb，风险较高）

### 2. 麦克风采集为静音
- 现象：`arecord -D capture` 录到的电平约为 1–2（满幅 32768），等于静音
- 排查过的：`Capture` 增益 0 → 35% / 100%；输入 Boost 开关 off/on；`ADC PCM` on
- 开着 Boost 时变成满幅噪声，说明收到的是底噪/自激，不是人声
- 判断：麦克风未接入正确输入、或需要 MICBIAS 偏置而板子未提供（mixer 里没有 bias 控件）
- **未做**：确认麦克风接的是哪个输入口（LINPUT1/2/3）、查 DTS 里的 micbias 配置

### 3. PL 路径偶发内存不连续
- 现象：`pl_stft: no 3 physically contiguous pages`，随后退回纯 ARM 路径
- 原因：长时间运行后物理内存碎片化
- 规避：重启板子；或改进驱动为分散页 + 多次 DMA

## 三、板子操作速查

串口：COM8 / 115200 / root:root

```sh
# 1. 停掉会抢声卡的队内服务
/etc/init.d/world-voice stop

# 2. 音频路由（否则完全没声）
amixer -c 0 sset 'Left Output Mixer PCM' on
amixer -c 0 sset 'Right Output Mixer PCM' on
amixer -c 0 sset Speaker 100%
amixer -c 0 sset Headphone 100%
amixer -c 0 sset Playback 100%
amixer -c 0 sset Capture 35%
amixer -c 0 sset 'ADC PCM' on

# 3. 跑一次转换（文件进文件出）
VC_PL=1 /tmp/vc/vc_pl_dbg3 4 native_s24 200 --stream 300 \
  --model /tmp/vc/student_v5_o64.blob --preset live \
  < /tmp/vc/in.raw > /tmp/vc/out.raw

# 4. 播放（PL 报内存错时用 VC_PL=0 退回纯 ARM）
aplay -D default -t raw -f S24_LE -r 32000 -c 2 /tmp/vc/out.raw

# 5. 采集设备名是 capture（不是 default）；hw:0,0 播放 / hw:0,1 采集
arecord -D capture -t raw -f S24_LE -r 32000 -c 2 /tmp/vc/mic.raw
```

## 四、串口上传注意
- 一次发送超过约 30 字符会偶发字符重复（`sh` → `ssh`），必须分小块发送（每片 ≤30 字符，间隔 50 ms）
- 上传大文件用 base64 分片，实测约 7.6 KB/s

## 五、交付物位置（原机器）
- 参赛包：`competition_pkg_20261026/`
- 代码压缩包：`competition_submit_20261027.rar`
- 技术文档草稿：`competition_submit_20261027/tech_report.pdf`
