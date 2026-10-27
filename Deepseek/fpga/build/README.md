# fpga/build — 位流与交付物

> **状态（2026-10-27）：本目录的变调核是"已验证的备用设计"，不是当前入链版本。**
> 当前入链的是 `fpga/stft/`（PL 承担 STFT/IFFT + 包络乘法）。
> 两版**不能共存**：它们占同一个 PL、共用 PS7/I2S/DMA/GPIO，同一时刻只能加载一个位流；
> 切换必须重新加载 `fpga_manager` 镜像并重启音频消费者。关于"为什么 PL 做 FFT 而不是变调"，
> 见 `fpga/stft/README.md` §6 与设计报告 §6.8。

## 1. 内容

| 文件 | 大小 | SHA-256（前 16） | 说明 |
|---|---|---|---|
| `audio_pitch.bit` | 4,045,672 B | `406667b4657e3623` | Vivado 位流（JTAG / 调试用） |
| `audio_pitch.bin` | 4,045,564 B | `ce1552c9e4b5559f` | 原始 `.bin`（大端 32 位字） |
| `audio_pitch_dma_2018_swap.bin` | 4,045,564 B | `8aedb87d4144dd74` | **Zynq `fpga_manager` 用**：每 4 字节反转 |
| `audio_pitch_dma_2018_swap.bin.gz` | 332,294 B | `faf6c27130bb594a` | 同上，gzip（串口上传用） |
| `audio_pitch.hdf` | 827,497 B | `2545a57e95ed60b4` | 2018.3 硬件平台导出 |
| `audio_pitch.hwdef` | 437,549 B | `95675dcfe846ae03` | 硬件定义 |
| `SHA256SUMS.txt` | — | — | 全部产物 + 源码的校验和清册 |
| `build_pl.ps1` | — | — | 一键重建（4 个 Tcl + make_swap + SHA 对照） |

`.bit` 文件头（只读解析）：

```
a = zynq_wrapper;UserID=0XFFFFFFFF;Version=2018.3
b = 7z020clg400
c = 2026/10/25   d = 23:18:09
payload = 4045564 B
```

## 2. 怎么用

### 2.1 直接加载（不再综合）

```powershell
# 板上（root）：把 .gz 传到 /tmp 后
gunzip -c audio_pitch_dma_2018_swap.bin.gz > audio_pitch_dma_2018_swap.bin
python3 prepare_recovery.py /tmp/pl_2018        # 生成回滚镜像（只读启动分区）
python3 load_pl_2018.py /tmp/pl_2018 /tmp/pl_2018/audio_pitch_dma_2018_swap.bin
```

或用技能包里的通用加载器（含回滚、寄存器验收）：

```powershell
cd /tmp/pl_2018
python3 overlay.py --image /tmp/pl_2018/audio_pitch_dma_2018_swap.bin --run-dir /tmp/pl_2018 `
  --consumers consumers.txt --rebind "41600000.i2c 43c20000.axi_dynclk 43c50000.i2s_receiver 43c60000.i2s_transmitter 43c40000.audio_formatter xlnx_snd_card.0.auto"
python3 regtool.py regmap.json          # 或 ./regtool --base 0x41200000 --check ...
```

### 2.2 从源码重建

```powershell
.\build_pl.ps1                                    # 默认 D:\pl_build_try
.\build_pl.ps1 -Work D:\pl_try2 -Vivado "D:\Vivado\Vivado\2018.3\bin\vivado.bat"
```

> **预期**：资源与时序应复现（LUT ±几个百分点，WNS 同号同量级）；
> **位流的 SHA 会不同**——布线在不同机器/不同 build 上不可位复现。这不是错误。

## 3. 资源与时序（本次交付的位流）

| 指标 | 综合 | 实现 | 占比 |
|---|---|---|---|
| Slice LUTs | 9374 | **8378** | 15.75% |
| Slice Registers | 14506 | **13286** | 12.49% |
| Block RAM Tile | 5 | **5** | 3.57% |
| DSPs | 6 | **6** | 2.73% |
| Bonded IOB | 12 | 12 | 9.60% |
| WNS / WHS / WPWS | +3.750 / +0.035 / +0.530 ns | **+0.813 / +0.045 / +0.530 ns** | 0 failing endpoints |
| DRC | — | 0 Error / 0 Critical Warning | 6 条建议级 DSP 流水线提示 |

时钟：`clk_fpga_0` = 100 MHz（10.000 ns），扇出 13186。
原始报告：`../report/{synth,impl}_{utilization,timing,drc}.txt`。

## 4. 加载验证记录（2026-10-25）

| 检查 | 结果 |
|---|---|
| `fpga_manager/fpga0/state` | `operating → operating` |
| dmesg | `writing audio_pitch_dma_2018_swap.bin ...`，无 oops |
| 旧 PL 消费者 | 18 个全部 unbind |
| 音频驱动回绑 | 6 个，`/dev/snd/controlC0` 存在 |
| AXI GPIO 回读 | 5/5 组精确一致（初值 86856） |
| DMA 端到端 | **128000 样本 max_abs_diff = 0**（三个比例） |
| 吞吐 | 4.10 M 样本/s（RTF 0.0078） |

原始日志在 `../../metrics/logs/pl_build/`。

## 5. 回滚

两种方式，都不需要改启动分区：

1. **冷重启**：U-Boot 从 `/boot/bit/zynq7020.bit` 重新加载原厂位流（最彻底）。
2. **热回滚**：`prepare_recovery.py` 生成的 `factory_restore_swap.bin`
   （SHA `af275946c15ae958…`，与 2026-10-10 的历史记录一致），
   用 `fpga_manager` 写回，再按 GPIO/时钟→底层→上层顺序 rebind。

加载期间脚本会把 `panic` 设为 10 s：万一旧消费者 oops，板子自动重启并回到原厂位流。
