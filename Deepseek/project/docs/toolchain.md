# 工具链说明（含 2018.3 的合规说明）

赛题要求：Vivado / Vitis **2026.1（推荐）或 2025.2**；使用其它版本**必须在报告中说明，并保证脚本可复现**。
本作品使用 **Vivado 2018.3**，本文件是那份说明。

---

## 1. 为什么是 2018.3

| 原因 | 说明 |
|---|---|
| 唯一完整安装 | 本机可用的完整 Vivado 安装只有 2018.3（`D:\Vivado\Vivado\2018.3`），没有 2025.2/2026.1 的授权与安装 |
| 风险权衡 | 比赛窗口内升级工具链，需要重新验证 IP 版本、BD、约束、位流与时序，且新版本对 `-2` 器件的速度文件与 DRC 规则有差异；风险大于收益 |
| 结论 | 用 2018.3 完成**全部**综合、实现、位流与上板验证，并**把每一步的 Tcl 与原始报告入库**，保证换版本可复现 |

### 1.1 三条可核对的技术理由（不是"懒得升级"）

| # | 事实 | 在哪个文件能看到 |
|---|---|---|
| 1 | 2018.3 的 batch 模式没有 `write_hw_platform`，只有 `write_hwdef` + `write_sysdef`；本包的 `.hdf` 是用后两者生成的等价物 | `fpga/src/bd/export_hdf.tcl`、`metrics/logs/pl_build/export_hdf.log` |
| 2 | 2026 版脚本请求的 `axi_iic:2.1` 在 2018.3 的 IP 目录里不存在，本包保留 `2.0` | `fpga/src/bd/create_audio_pitch_dma.tcl` 注释、§2.1 |
| 3 | 位流头里写着生成工具与器件（`Version=2018.3` / `7z020clg400`），与实现报告的时间戳、Host 名一起构成"这份报告确实来自这个位流"的证据链 | `fpga/build/SHA256SUMS.txt`、`fpga/stft/report/impl_utilization.txt` 头部 |

> 换句话说：**换版本不是改一行版本号**。这三条决定了"换成 2026.1 要重新做哪几件事"，
> 而不是"数字大概不会变"。§6 给的是换版本时按顺序要做的核对。

---

## 2. 版本差异与处理（逐项核对过）

### 2.1 IP 版本：**一个都不用改**

在 2018.3 的 `data/ip/xilinx` 目录里逐个确认脚本请求的 VLNV 都存在：

| IP | 脚本请求 | 2018.3 是否自带 | 处理 |
|---|---|---|---|
| processing_system7 | 5.5 | ✅ | 未改 |
| audio_formatter | 1.0 | ✅ | 未改 |
| i2s_receiver | 1.0 | ✅ | 未改 |
| i2s_transmitter | 1.0 | ✅ | 未改 |
| axi_dma | 7.1 | ✅ | 未改 |
| **axi_iic** | **2.0**（2026 版脚本用 2.1） | 2018.3 **没有 2.1** | **保持 2.0** |
| axi_interconnect | 2.1 | ✅ | 未改 |
| proc_sys_reset | 5.0 | ✅ | 未改 |
| util_vector_logic / xlconstant / xlconcat | 2.0 / 1.1 / 2.1 | ✅ | 未改 |
| axi_dynclk | `digilentinc.com:ip:axi_dynclk:1.2` | 由本地 `ip_repo` 提供 | 未改 |

> 换到 2026.1 时，`axi_iic` 可能需要 2.1、`axi_gpio` 可能升版；
> 其余脚本可直接用。**这是唯一预期需要改动的地方**，写在 `fpga/src/bd/create_audio_pitch_dma.tcl` 的注释里。

### 2.2 `write_hw_platform` 不存在

2018.3 的 batch Vivado 里没有 `write_hw_platform -fixed -include_bit`：

```
write_hw_platform note: invalid command name "write_hw_platform"
```

可用的是 `write_hwdef` + `write_sysdef`，因此 `fpga/src/bd/export_hdf.tcl` 用它们生成
等价交付物 `.hdf`（827,497 B）+ `.hwdef`（437,549 B）。
2018.3 的 `.xsa` 需要 SDK/Vitis 侧 `hsi` 打包，batch 里不做。

### 2.3 BD 唯一的设计改动

> **状态（2026-10-27）**：本节描述的是**备用变调核**（`fpga/src/`）的 BD 改动。
> 当前入链的 **STFT 版**（`fpga/stft/`）从同一个已验证的 `audio_pitch_dma` BD 派生，
> PS7 / I2S / DMA / GPIO 地址不变，只把 stream 核换成 `axis_stft_gain` + 两个 xfft
> （见 `fpga/stft/README.md` 与 `PL_STFT_20261027.md`）。

不是版本兼容问题，而是"要能写 ratio 并读回"：把固定比例的 `xlconstant` 换成
**AXI GPIO@0x41200000**（ch1=ratio_q16 18 位，ch2=scratch 1 位，`C_DOUT_DEFAULT=0x15348`）。
**变调核 RTL 一行未改。** 四处改动与原因见 `fpga/report/build_changes_2018_3.md`。

### 2.4 位流格式与加载

- Vivado `.bin` 是**大端 32 位字**，Zynq `fpga_manager` 要**小端** → 每 4 字节反转
  （`fpga/src/make_swap.py`，校验 `aa995566` → `665599aa`）。
- 反转后再 gzip（4,045,564 → 332,294 B），串口上传 42.4 s。
- `.bit` 文件头已核：`zynq_wrapper;UserID=0xFFFFFFFF;Version=2018.3` / `7z020clg400`。

---

## 3. 构建命令（三行，全部入库）

```powershell
$viv = "D:\Vivado\Vivado\2018.3\bin\vivado.bat"
& $viv -mode batch -source fpga\src\bd\create_audio_pitch_dma.tcl -log logs\create.log
& $viv -mode batch -source fpga\src\bd\synth_2018_3.tcl          -log logs\synth.log
& $viv -mode batch -source fpga\src\bd\impl_2018_3.tcl           -log logs\impl.log
& $viv -mode batch -source fpga\src\bd\export_hdf.tcl            -log logs\export.log
python fpga\src\make_swap.py <impl_1>\zynq_wrapper.bin fpga\build\audio_pitch_dma_2018_swap.bin
```

一键脚本：`fpga/build/build_pl.ps1`（会做 SHA 核对与产物清单）。

预期输出标记（脚本里会打印）：
`AUDIO_PITCH_DMA_VALIDATED` → `AUDIO_PITCH_DMA_SYNTHESIZED_2018_3` →
`AUDIO_PITCH_DMA_BITSTREAM_BUILT_2018_3` → `HDF_EXPORTED`。

---

## 4. PS 侧工具链

```powershell
# 交叉编译（静态 ARM，无 INTERP 段）
.\host\app\build_arm.ps1          # 产物 host\app\build\vc_stream_arm
# 主机侧同源码构建（数值迭代用）
.\host\app\build_host.ps1
```

- 编译器：`D:\Vivado\SDK\2018.3\gnu\aarch32\nt\gcc-arm-linux-gnueabi\bin\arm-linux-gnueabihf-g++.exe`
- 关键链接参数：`-static -s -Wl,--gc-sections -Wl,--whole-archive -lpthread -Wl,--no-whole-archive -lm`
  （`--whole-archive` 是为了让静态 glibc 下的 `pthread_create` 真的可用，见 `report/failure_analysis.md`）
- 产物校验：ELF magic / `e_machine=0x28` / `e_type=EXEC` / flags `0x05000400` / SHA-256。

板端 C 工具（`host/deploy/`）：`pitch_dma_mem.c`、`gpio_check.c`、`regtool.c`、`dma_roundtrip.c`，
编译命令见各自文件头；本包已在 2018.3 SDK 的 GCC 7.3.1 上交叉编译并核对
**`pitch_dma_mem` 重编译产物与板上运行的二进制逐字节相同**（SHA `fe312bb1…`）。

> `vc_stream_arm`（C++）重编译后**大小相同、SHA 不同**：C++ 局部静态符号名参与布局，
> GCC 的随机种子默认由输入路径派生，换目录重编译就会变。这不影响功能，
> 但意味着"用二进制 SHA 证明复现"只对单文件 C 工具成立。见 `host/app/build/BUILD_NOTE.md`。

---

## 5. 复现性核对表

| 项 | 期望值 | 怎么核 |
|---|---|---|
| `.bit` 大小 / SHA（备用变调核） | 4,045,672 B / `406667b4…` | `Get-FileHash` |
| `.bin` SHA | 4,045,564 B / `ce1552c9…` | 同上 |
| 加载镜像（swap）SHA | 4,045,564 B / `8aedb87d…` | 同上 |
| `.hdf` SHA | 827,497 B / `2545a57e…` | 同上 |
| 综合资源（变调核） | 9374 LUT / 14506 FF / 5 BRAM / 6 DSP | `fpga/report/synth_utilization.txt` |
| 实现资源（变调核） | 8378 LUT / 13286 FF / 5 BRAM / 6 DSP | `fpga/report/impl_utilization.txt` |
| 时序（变调核） | WNS +0.813 / WHS +0.045 / 0 failing | `fpga/report/impl_timing.txt` |
| **STFT 位流 `.bit`（当前入链）** | 4,045,672 B / `346e40c2…` | `fpga/stft/SHA256SUMS.txt` |
| **STFT `.bin`** | 4,045,564 B / `89d6f0c1…` | 同上 |
| **STFT swap 镜像 `.bin.gz`** | 568,326 B / `da1701f2…` | 同上 |
| **STFT 实现资源** | 16,723 LUT / 28,677 FF / 22 BRAM / 76 DSP | `fpga/stft/report/impl_utilization.txt` |
| **STFT 时序** | WNS **+0.347** / WHS +0.040 / 0 failing | `fpga/stft/report/impl_timing.txt` |
| 权重 blob（T4/48 阶） | 4,843,308 B / `c04107b9…` | `Get-FileHash` |
| 权重 blob（O64/64 阶） | 4,941,804 B / `01aecb78…` | `host/model/student_v5_o64.json` |

全部原始报告在 `fpga/report/` 与 `fpga/stft/report/`，校验和清单在
`fpga/build/SHA256SUMS.txt` 与 `fpga/stft/SHA256SUMS.txt`。

---

## 6. 如何保证"换机器 / 换版本还能复现"（四道锁）

| # | 锁 | 具体做法 | 今天怎么验（不用重跑 Vivado） |
|---|---|---|---|
| 1 | **构建脚本全入库、路径参数化** | `fpga/src/bd/*.tcl`、`fpga/stft/tcl/*.tcl` 全部入库；工作目录由 `build_pl.ps1 -Work <dir>` 指定，不写死本机路径（默认值只是方便） | 打开 `fpga/build/build_pl.ps1` 看 `param([string]$Work=…)`；Tcl 里没有 `D:\` 绝对路径（`grep` 可验） |
| 2 | **IP 版本逐项核对** | §2.1 的 10 个 IP 在 2018.3 目录里逐个确认存在；唯一的差异（`axi_iic` 2.0 vs 2.1）写在脚本注释里 | 读 §2.1 表 + `create_audio_pitch_dma.tcl` 的 VLNV 行 |
| 3 | **原始报告入库 + 数字可重抽取** | 综合/实现/DRC/时序/时钟/总线偏斜的**原始文本**都在 `fpga/report/`、`fpga/stft/report/`；`collect_metrics.py` 能把这些数字重新抽成 CSV | `metrics/README.md` §4 的命令重跑，产出与本包 `resource_timing.csv` **51/51 行一致**（2026-10-27 实测） |
| 4 | **位流 SHA + 可加载镜像规则** | `.bit`/`.bin`/swap/`.hdf` 都有 SHA；`.bin → swap` 的 4 字节反转规则脚本化（`make_swap.py`，校验 `aa995566`→`665599aa`），gzip 后的镜像就是在板上跑的那一份 | 按 §5 表用 `Get-FileHash` 逐个比 |

**明确不保证的一件事**：位流**不是位级可复现的**。同一份 Tcl、同一版本、同一机器，
重新 place & route 出来的 SHA 通常也会不同（布线种子/机器相关）。所以本包的承诺是：

- **资源与时序数字**可复现到几个百分点（两份原始报告都在，可对照）；
- **功能行为**可复现到逐样本（`m3_compare_clean.txt` 的 `max_abs_diff 0`、
  STFT 版 `corr 0.99999999 / max 4 LSB`）；
- **位流 SHA** 只用于"你手上这份没被改过"，不用于"你必须编译出同一个 SHA"。

### 换到 2026.1 / 2025.2 的迁移顺序（如果评委会这么要求）

1. 先跑 `create_audio_pitch_dma.tcl`：报 VLNV 错就把 `axi_iic` 升到 2.1、`axi_gpio` 按提示升版；
2. 再跑综合/实现：先看 `synth_utilization.txt` 的 LUT/BRAM/DSP 是否与 2018.3 同量级（±5%），
   再看 WNS 是否仍为正；
3. `.hdf` 换成 `write_hw_platform -fixed -include_bit`（2026 版有这条命令），
   `export_hdf.tcl` 里加一个版本分支即可；
4. 上板前用 §5 的 SHA 表确认加载的是新编的镜像，别把旧镜像当新结果；
5. 报告里把"工具版本"一栏改成实际用的版本，并说明"资源/时序与 2018.3 的差异在 x% 以内"。
