# fpga/stft — PL STFT/ISTFT + 逐 bin 包络乘法（2026-10-27）

**状态：已上板、已入链。** 本目录是"PL 承担 STFT/IFFT + 频域乘法"这一版
的完整交付；`fpga/build/`、`fpga/src/` 下的**定点变调核**改为**备用设计**
（见 §6，两版**不能同时加载**）。

来源：`<workspace>/pl_stft_20261027/`（实验产物，只读复制）；
构建根：`D:\g_build\pl_stft_20261027`（Vivado 2018.3，短 ASCII 路径是硬要求）。
原始报告：本目录 `PL_STFT_20261027.md`（逐字复制自
`<workspace>/pl_stft_20261027/`，下称 `PL_STFT_20261027.md`；
本目录所有数字均出自该报告 §5/§6）。

## 1. 它做什么

主链 STFT 是 `n_fft=1024, hop=160, periodic Hann, center=True`，包络移植是
**每个 (帧,bin) 的实数增益**。因此 PL 只需做「前向 FFT → 乘实数增益 → 逆 FFT」，
窗、重叠相加（OLA）、`wsum` 归一化仍留在 ARM：

```
ARM: 窗 + int16 量化 + 增益 Q4.19 量化 ──AXIS──► PL: 1024 点 FFT (24 bit in, unscaled)
                                                    → 逐 bin 乘 g_q (Q4.19)
                                                    → 1024 点 IFFT (32 bit in, unscaled)
ARM: OLA + wsum 归一化 ◄──AXIS── PL: z·256 (int32)
```

每帧输入 1537 words（1024 样本 + 513 增益），输出 1024 words；实测
**8715 cycles/帧 = 87 µs**（10 ms 帧预算的 0.87%）。

## 2. 关键数字（全部出自 PL_STFT_20261027.md）

| 项 | 值 | 来源 |
|---|---|---|
| 端到端一致性（同一 `in.raw`、同一模型，128000 样本左声道） | **corr 0.99999999 / max 4 LSB / rms 0.60 LSB** | §5.1 |
| STFT 段耗时 | **449.04 → 305.82 ms**（−31.9%；其中 PL DMA 往返 75.63 ms） | §5.1 |
| 整链（4 s） | total **3750.29 → 3607.80 ms**，**RTF 0.9376 → 0.9019** | §5.1 |
| 稳定性 | 8×4 s = 32 s：0 失败、8/8 输出逐字节相同、RTF 0.904 | §5.3 |
| 资源（impl） | **16,723 LUT (31.4%) / 22 BRAM (15.7%) / 76 DSP (34.6%)** | §6 |
| 时序（impl） | **WNS +0.347 ns** / WHS +0.040 ns，100 MHz，0 failing endpoints | §6 |

## 3. 目录

| 路径 | 内容 |
|---|---|
| `rtl/axis_stft_gain.v` | 帧引擎（收样本/收增益/乘法/输出 FSM，纯 RTL） |
| `rtl/fft_pair.v` | M1 单独 OOC 用的 FFT 对包装 |
| `tcl/ip_fft.tcl` | 两个 xfft 9.1 实例的唯一创建入口（24 bit 前向 / 32 bit 逆向，均 unscaled） |
| `tcl/create_stft_dma.tcl` | BD：从已验证的 `audio_pitch_dma` 派生，FFT 作独立 IP cell |
| `tcl/synth.tcl` / `impl.tcl` | 综合 / 实现 / 出位流与 `.hwdef` |
| `tcl/ooc.tcl`、`sim*.tcl` | OOC 与 M1 逐 bin 仿真 |
| `bitstream/stft_dma.bit` | Vivado 位流（JTAG / 调试） |
| `bitstream/stft_dma.bin` | 原始 `.bin`（大端 32 位字） |
| `bitstream/stft_dma_swap.bin` | **Zynq `fpga_manager` 用**：每 4 字节反转 |
| `bitstream/stft_dma_swap.bin.gz` | 同上 gzip（串口上传用，568 KB） |
| `bitstream/stft_dma.hwdef` | 硬件定义 |
| `bitstream/vc_o64_pl` | 入链后的 ARM 二进制（`-DVC_PL_DEFAULT=1`，812,624 B） |
| `board/build_pl.ps1` | 交叉编译 `vc_o64_pl`（用本包 `host/app/` 的 WORLD/SoundTouch） |
| `board/src/vc_stream_pl.cpp`、`pl_stft.cpp` | 打了 `--pl-stft` 分支的主链 + PL 调用层 |
| `board/load_pl_2018.py`、`prepare_recovery.py` | 加载 / 回滚镜像生成 |
| `report/impl_*.txt`、`synth_*.txt` | 原始资源/时序/DRC 报告 |
| `tools/make_swap.py`、`prep_bitstream.ps1` | `.bin` → `fpga_manager` 镜像（4 字节反转 + gzip） |
| `SHA256SUMS.txt` | 本目录全部产物的校验和 |

## 4. 重建（Vivado 2018.3，**不要**在长中文路径下建 BD）

```powershell
# 构建根必须是短 ASCII 路径（实测在 <workspace>/... 下子 IP 的 OOC 综合会崩：
# TclStackFree / PS7 DCP 不生成）。把本目录整体拷到 D:\g_build\stft\ 后：
cd D:\g_build\stft
& 'D:\Vivado\Vivado\2018.3\bin\vivado.bat' -mode batch -source tcl\create_stft_dma.tcl
& 'D:\Vivado\Vivado\2018.3\bin\vivado.bat' -mode batch -source tcl\synth.tcl
& 'D:\Vivado\Vivado\2018.3\bin\vivado.bat' -mode batch -source tcl\impl.tcl
# 位流落在 bitstream\stft_dma.bit / .bin，资源/时序报告落在 report\
powershell -ExecutionPolicy Bypass -File tools\prep_bitstream.ps1   # 生成 swap.bin + .gz
```

Tcl 里的 `$root` 是"本目录的上一级"，即把 `tcl/` 放在 `<root>/tcl/` 即可，
`bitstream/`、`report/`、`board/vendor_inputs/` 都会被自动定位。

## 5. 上板加载与回退

```sh
# 板端（root，先 /etc/init.d/world-voice stop）
python3 /tmp/pl_2018/load_pl_2018.py /tmp/pl_2018 /tmp/pl_2018/stft_dma_swap.bin
cat /sys/class/fpga_manager/fpga0/state      # 期望 operating
./vc_o64_pl 4 native_s24 200 --pl-stft --model student_v5_o64.blob < in.raw > /dev/null
```

镜像 SHA-256（与 `PL_STFT_20261027.md` §8 一致）：

```
stft_dma_swap.bin      d597cb0af256e4b62b44b26a511696e5a528fa264df27626989b33e6008f1c7e
stft_dma_swap.bin.gz   da1701f28b3e6c482e9d728187c708c496b3f667fe514689160f56bdc35c1d5c
```

回退（镜像互斥，见 §6）：

```sh
python3 /tmp/pl_2018/load_pl_2018.py /tmp/pl_2018 /tmp/pl_2018/audio_pitch_dma_2018_swap.bin  # 回变调核
python3 /tmp/pl_2018/load_pl_2018.py /tmp/pl_2018 /tmp/pl_2018/factory_restore_swap.bin        # 回原厂
```

## 6. 与变调核的关系：**互为备用，不能共存**

- 两版是**同一个 PL 上的两套不同 stream 核**（`axis_stft_gain` + 2×xfft ↔ `axis_pitch_shift`），
  共用 PS7 / I2S / DMA / GPIO 地址。**同一时刻只能加载一个位流**；切换必须重新
  加载 `fpga_manager` 镜像并重启音频消费者（`aplay`/`vc_*`）。
- **变调核**（`fpga/build/audio_pitch_dma_2018_swap.bin`，SHA `8aedb87d…`）是**已验证的备用设计**：
  bit-exact、4.10 M 样本/s、RTF 0.0078，但**未接入主链**（主链升调仍由 ARM SoundTouch 完成）。
- **STFT 版**是当前入链版本：不改变音质路径（FFT/IFFT 与 ARM 双精度 STFT 数学等价），
  只把 FFT 搬到 PL，因此一致性 corr 0.99999999 / max 4 LSB。
- 为什么 PL 做 FFT 而不做变调：变调核是**相位声码器式的重采样**，会改变波形相位、
  伤音质且与 ARM 参考链不等价；FFT 只是同一变换的定点实现，**数学等价、可逐样本比对**，
  风险与收益都更可控（详见 `PL_STFT_20261027.md` §1 与设计报告 §6.8）。
