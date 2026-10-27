# 硬件与板级环境

## 1. 硬件清单

| 项 | 型号 / 参数 | 说明 |
|---|---|---|
| 开发板 | 野火皓月 Zynq-7020 | `xc7z020clg400-2`，双核 A9 @667 MHz，1 GB DDR3 |
| 音频 codec | WM8960（板载） | I2S + I2C 控制，经 PL 的 `audio_formatter`/`i2s` 接到 PS |
| 麦克风 | 3.5 mm 模拟麦（粉色口 **J12**） | 走 WM8960 **LINPUT1**；板载咪头 P1 **不可用**（另一条输入支路） |
| 音箱 / 耳机 | 3.5 mm（绿色口 **J13**） | WM8960 耳机输出 |
| 串口 | USB-UART，主机侧 **COM8** | 115200 / 8N1 / 无流控，登录 `root`（密码 `root`） |
| 存储 | microSD（PetaLinux 2022.2 镜像） | `/boot/bit/zynq7020.bit` 为原厂位流（只读使用） |
| 供电 | 12 V DC | 板上 5 W 级 |

> 板载咪头与 J12 走的是**不同的输入支路**，如果只开其中一路的供电/路由，
> 现象是"录到全 0 或只有底噪"。这一条在历史调试里花过时间（见
> `ai_collaboration/05_tooling_and_traps.md`）。

## 2. 软件版本（必须与报告一致）

| 项 | 版本 |
|---|---|
| 板端系统 | PetaLinux 2022.2，内核 `5.15.0-xilinx` |
| 交叉编译器 | Linaro GCC 7.3.1（Vivado SDK 2018.3 自带：`arm-linux-gnueabihf-g++`） |
| 主机综合工具 | Vivado 2018.3（SW Build 2405991） |
| 主机 Python（评测） | 3.12 + torch / pyworld 0.3.5 / librosa（`env/venv`） |
| 板端 Python | 3.x，**无 `mmap` 模块**（所以寄存器/ DMA 工具用静态 C） |

## 3. 接线

```
        ┌──────────────────────────────┐
        │      野火 Zynq-7020           │
  MIC ──┤ J12 (粉, LINPUT1)            │
        │                     J13 (绿) ├── 耳机 / 有源音箱
  USB ──┤ J-USB-UART  ──► 主机 COM8     │
  12V ──┤ DC 输入                       │
        └──────────────────────────────┘
```

- 麦克风插 **粉色 J12**（不是板载咪头）。
- 耳机/音箱插 **绿色 J13**。
- 串口线插板上的 USB-UART 口，主机侧识别为 COM8（设备名可能随 USB 口变化，用前确认）。

## 4. 板级操作前置检查（每次都做，30 秒）

```sh
# 0) 串口独占：主机侧确认没有别的进程占用 COM8（串口助手/上一个会话）
#    板上确认没有残留的 aplay/arecord 占着声卡
ps | grep -E 'aplay|arecord|vc_live' | grep -v grep

# 1) 停掉会独占声卡的演示服务（它会把 Subdevices 占成 1/1）
/etc/init.d/world-voice stop

# 2) 看声卡状态
aplay -l
cat /proc/asound/card0/pcm0p/sub0/status
cat /proc/asound/card0/pcm1c/sub0/status

# 3) 保存当前 mixer（结束时恢复）
alsactl -f /tmp/vc/mixer_before.state store 0

# 4) 确认 PL 状态
cat /sys/class/fpga_manager/fpga0/state     # 期望 operating

# 5) 确认临时盘空间（/tmp 是 tmpfs，掉电即失）
df -h /tmp
```

**结束必做**（不靠记性，写进脚本）：

```sh
alsactl -f /tmp/vc/mixer_before.state restore 0
stty echo                       # 串口会话被 Ctrl-C / 续行卡过之后一定要恢复
# 需要演示时把服务起回来：
/etc/init.d/world-voice start
```

## 5. 音频路由与增益

| 环节 | 设置 | 备注 |
|---|---|---|
| 采集 | `arecord -D hw:0,1 -t raw -f S24_LE -r 32000 -c 2` | `S24_LE` = 32-bit 容器 + 24 位有效**左对齐** |
| 播放 | `aplay -D default -t raw -f S24_LE -r 32000 -c 2` | |
| 起播预填充 | `--start-delay=64000`（= 2 s @32 kHz 帧） | 与 `--stream` 块长无关；试过 2/3/4 s，对欠载无改善 |
| 输出增益 | `out_gain_q16 = 39322`（0.6） | 默认值；单位增益 65536 会削波（峰值 1.36 FS） |
| 输入增益 | 麦克风用 `in_gain_q16 ≈ 262144`（4×） | 板上麦克风实测只有 **−42 dBFS** 底噪，必须抬电平 |
| Codec 采集增益 | 历史配置 `Capture 39`（+12 dB 档位，TLV：min −17.25 dB / step 0.75 dB） | 仅作为历史对照记录；本作品不依赖它 |

> **电平纪律**：输出削波会让 UTMOS/CER 变差，输入电平过低会让模型把噪声当语音。
> 每次换场地都要重测一次 `peak_out` 与 `voiced_frames`（遥测里有）。

## 6. 串口传输能力（决定迭代节奏）

| 内容 | 大小 | 耗时 | 速率 |
|---|---|---|---|
| 二进制（`vc_live`） | 726–804 KB | 93–95 s | 7.67–7.80 KB/s |
| 权重 blob | 4,843,308 B | 621 s（≈10.3 min） | 7.80 KB/s |
| 1 MB 测试音频 | 1,024,000 B | 132.5 s | 7.73 KB/s |
| 位流（gzip 后） | 332,294 B | 42.4 s | — |

**因此**：日常数值迭代必须用主机侧 `vc_stream_host.exe`（同一份源码），
只有定版才上板。`/tmp` 是 tmpfs，**每次重启都要重传权重（10 min）**。

## 7. 常见板级故障对照

| 现象 | 原因 | 处理 |
|---|---|---|
| `aplay` 报 device busy / `Subdevices: 1/1` | `world-voice` 演示占着声卡 | `/etc/init.d/world-voice stop` |
| 串口命令全部超时 | 上一个进程占着 COM8，或板端 shell 停在续行 | 主机侧确认独占；板上 Ctrl-C + `stty echo` |
| 录到全 0 或只有底噪 | 麦克风插错口 / 该支路 MICBIAS 未开 / 电平太低 | 确认 J12；`in_gain_q16=262144` |
| 输出削波（`clipped_samples>0`） | 用了单位增益 | `out_gain_q16=39322` |
| `fpga_manager` 加载后不是 `operating` | 镜像没做 4 字节反转 / 旧消费者没解绑 | 用 `skill/overlay_load_and_verify` 的校验与 unbind 流程 |
| 输出偶发 8 样本全 0 | L2 脏行回写 | 见 `skill/dma_cache_coherency/diag_checklist.md` §1 |
| 重启后权重不见了 | `/tmp` 是 tmpfs | 重传（10 min），或改用 SD 卡持久目录 |
| 摄像头 `ov5640 failed to read chip identifier` | 本设计里没有摄像头 | **预期噪声**，忽略 |

## 8. 环境约束（对复现者的提醒）

1. **本包不包含 PetaLinux 镜像与 SD 卡内容**，只包含 PL 位流、PS 程序、模型与脚本。
   复现者需要一块已烧好 PetaLinux 2022.2（或等价）的 7020 板。
2. **`/dev/mem` 需要 root**；`regtool`/`pitch_dma_mem` 都以 root 运行。
3. **串口不是必须的**：如果能用网口/SCP，上传 4.6 MB 权重只需几秒，不必忍受 7.8 KB/s。
   本包的脚本用串口是因为现场只有串口。
4. 板端新增文件全部写在 `/tmp/`，**未改启动分区、未改系统文件**；
   撤离时删掉 `/tmp/vc`、`/tmp/pl_2018` 即可完全还原。
