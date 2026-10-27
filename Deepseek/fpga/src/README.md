# fpga/src — RTL、BD 构建脚本与工具

> **状态（2026-10-27）：本目录是变调核（备用设计）。** 当前入链的是
> `fpga/stft/`（PL 承担 STFT/IFFT + 逐 bin 包络乘法）。两版**不能同时加载**
> （同一 PL、同一套 PS7/I2S/DMA/GPIO），切换需重载位流；原因见 `fpga/stft/README.md` §6。

## 1. 目录

```
fpga/src/
├── rtl/
│   ├── axis_pitch_shift.v      变调核（143 行，定点 Q16 相位 + 线性插值）
│   ├── pcm_delay_ram.v         2048×16 环形 RAM（同步读写，推断为 BRAM）
│   ├── axis_audio_bypass.v     AXI-Stream 旁路（仿真/回环测试用）
│   └── my_iobuf.v              板级 IOBUF 原语封装
├── bd/
│   ├── create_audio_pitch_dma.tcl  建 BD + wrapper + validate（含 AXI GPIO 改动）
│   ├── synth_2018_3.tcl            综合入口（2018.3）
│   ├── impl_2018_3.tcl             实现 + 位流入口
│   ├── export_hdf.tcl              write_hwdef + write_sysdef（替代 write_hw_platform）
│   └── ps7_config.tcl              PS7 的 531 项配置（原厂值，未改）
├── constraints/
│   └── audio_i2c.xdc               24 条引脚约束
├── make_swap.py                    .bin → fpga_manager 镜像（4 字节反转 + gzip）
├── gen_test_audio.py               4 s 滑音测试信号（S24 双声道）
├── s24_to_pcm16.py                 S24 → PCM16（左声道）
└── compare_reference.py            RTL 的 Python 定点模型 + 逐样本比对
```

## 2. 设计要点（`axis_pitch_shift.v`）

- **接口**：AXI-Stream，PCM16 放 `tdata[15:0]`，`tkeep`/`tlast` 透传（见 `docs/interface.md` §1）。
- **状态机**：12 状态，复位后 CLEAR（2048 拍清零 RAM，≈20.5 µs @100 MHz）→ IDLE。
- **算法**：26-bit 相位累加器 + 2048 深环形 RAM + 两次线性插值（tap 与半窗 blend），
  与 `compare_reference.py` 的整数模型**逐位一致**。
- **旁路**：`ratio_q16 == 65536` 时直接转发输入（恒等测试用，输出 SHA 必须等于输入 SHA）。
- **越界保护**：`ratio_q16` 不在 32768–131072 时 `tready` 恒 0，流被挂起而不出坏数据。
- **定点纪律**（复核前人失败后定的）：所有乘法 `$signed()`；钳位双边；
  查表必插值且权重与地址同源；流水每级差一拍就用波形对齐一次。

## 3. 构建

```powershell
# 一键（4 个 Tcl + make_swap + SHA 对照）
..\build\build_pl.ps1 -Work D:\pl_try

# 或逐步（与交付位流完全相同的命令）
$viv = "D:\Vivado\Vivado\2018.3\bin\vivado.bat"
& $viv -mode batch -source bd\create_audio_pitch_dma.tcl -log create.log
& $viv -mode batch -source bd\synth_2018_3.tcl           -log synth.log
& $viv -mode batch -source bd\impl_2018_3.tcl            -log impl.log
& $viv -mode batch -source bd\export_hdf.tcl             -log export.log
python make_swap.py <impl>\zynq_wrapper.bin ..\build\audio_pitch_dma_2018_swap.bin
```

> 脚本用 `[file dirname [info script]]/..` 求 root，所以**保持目录结构**即可，
> 不需要改任何路径（2018.3 的构建就是这么做的）。

## 4. 与仓库原件的差异

只有 4 处，全在 `bd/create_audio_pitch_dma.tcl`（详见 `../report/build_changes_2018_3.md`）：

1. `xlconstant` → `axi_gpio:2.0`（18 位 ch1 + 1 位 ch2，`DOUT_DEFAULT=0x15348`）
2. `ctrl_ic` 的 `NUM_MI` 6 → 7，新增 `M06_AXI → ratio/S_AXI`
3. `ratio/dout` → `ratio/gpio_io_o` 接 `pitch/ratio_q16`
4. 地址分配新增 `0x41200000`

**RTL 一行未改**，PS7 配置、音频 Formatter/I2S/dynclk、DMA、引脚 XDC 全部未动。

## 5. 定点比对（改 RTL 后必跑）

```bash
python compare_reference.py work/input16_mono.raw work/output16_clean.raw 86856
# 期望: max_abs_diff 0 / samples_diff_gt2 0 / VERDICT PASS
```

比对前提：PL 处于**刚加载位流**的状态（本构建的 GPIO ch2 未接 `aresetn`，
`CONFIGURE` 不会清核内 RAM——见 `docs/interface.md` §2.2）。

## 6. 还留在仓库里但本包未使用的 RTL

`synth_offload/`（1024 点 IFFT、minphase exp 单元、twiddle ROM 等）属于**可行性验证**阶段的
产物，没有进入本交付的位流。其中 `minphase_exp_unit.v` 的"查表漏 frac 插值"是
`report/failure_analysis.md` F10 的原始案例，保留在仓库而不复制进本包，避免混淆。
