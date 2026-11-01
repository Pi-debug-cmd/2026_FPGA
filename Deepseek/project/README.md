# VC-7020：Zynq-7020 上的实时音色转换（2026 AMD 赛题参赛包）

> 在单颗 `xc7z020clg400-2` 上，把男声实时转换成**固定目标女声**的音色。
> PS 跑 WORLD + 倒谱 + MLP 算法链，**PL 承担 STFT/IFFT + 逐 bin 频域乘法**；
> 演示定版 **O64 + live 档**：300 ms 块、端到端 p99 584.8 ms、60 s 0 欠载。

| 维度 | 结果 | 状态 |
|---|---|---|
| 功能 | 4 s 批处理、23.72 s O64 整段、30 min 流式跑通，输出格式/长度正确（批处理削波 0；live 0.019%） | ✅ |
| 性能 | 4 s 批处理 **3857–3941 ms**（RTF **0.967–0.985**，T4/48 阶）；**O64 + live 3440 ms（RTF 0.860）**；O64 精确档 5380 ms（1.345） | ✅ |
| 实时 | 300 ms 块：T4 30 min **6000/6000 块、0 欠载**（p95 576.7 ms）；**O64 live 60 s 0 欠载、处理 p99 284.8 ms、端到端 p99 584.8 ms** | ✅ |
| PL | **STFT 版 16,723 LUT / 22 BRAM / 76 DSP、WNS +0.347 ns、corr 0.99999999 / max 4 LSB、STFT 段 449→306 ms**；变调核 8378/5/6 为备用（与 STFT 版互斥） | ✅ |
| 数值一致性 | C↔Python **121.71 dB**；ARM↔x86 **139.38 dB**；O64 板端↔Python O64 **corr 0.999999987 / 75.71 dB** | ✅ |
| 质量四指标（O64） | 精确档 identity 0.7293 ✅ / P10 0.6919 ✅ / 泄漏 −0.0223 ✅ / **UTMOS 2.2659 ❌**；live 档 0.7321 / 0.7006 / −0.0346 / **2.1900 ❌** | ⚠️ 部分 |
| 稳定性 | 3 次 ±0.1%；**T4 30 min 0 欠载**（6000/6000 块）；**O64 live 30 min 0 欠载、0 掉块、RSS 8,408 KB 恒定** | ✅ |
| 延迟分布 | T4：268.7 / 276.7 / 277.9 / 278.1 ms；**O64 live：276.0 / 284.0 / 284.8 / 286.8 ms**（60 s，200 块） | ✅ |

未达标项与缺口在 [`report/design_report.md`](report/design_report.md) §8 与
[`report/failure_analysis.md`](report/failure_analysis.md) 逐条列出，**没有隐瞒**。

---

## 1. 交付物一览

```
competition_pkg_20261026/
├── README.md                    ← 本文件：简介 + 从零复现 + 目录对照
├── MANIFEST.md                  ← 文件清单 / 体积 / 各目录计数 / 关键产物 SHA256
├── docs/                        架构 / 接口 / 硬件 / 工具链（含 2018.3 合规说明）
├── fpga/                        RTL + BD 构建 Tcl + 位流 + 综合实现报告
├── host/                        PS 主程序 + 模型权重 + 上板部署脚本
├── metrics/                     实测数据（CSV）+ 原始日志 + 脚本 + 图 + 被引用源报告
├── skill/                       ★ 三条可复用技能包（加分项）
├── report/                      设计报告 + 失败分析 + 提交自查表
└── ai_collaboration/            ★ 大模型协作记录（硬要求）
```

## 2. 目录对照（官方推荐结构 ↔ 本包）

| 官方推荐 | 本包位置 | 说明 |
|---|---|---|
| `README.md` | `README.md` | 本文件 |
| `docs/architecture.md` | `docs/architecture.md` | 系统架构图 + 数据流 + PS/PL 分工 |
| `docs/interface.md` | `docs/interface.md` | AXI-Stream / AXI-Lite 寄存器 / CLI 契约 |
| `docs/hardware_setup.md` | `docs/hardware_setup.md` | 板卡、接线、麦克风/音箱、串口、前置检查 |
| `fpga/src/` | `fpga/src/` | `rtl/`、`bd/`（建工程/综合/实现/导出 Tcl）、`constraints/` |
| `fpga/build/` | `fpga/build/` | `.bit`/`.bin`/`.hdf`/swap 镜像/`SHA256SUMS.txt`/`build_pl.ps1` |
| `fpga/report/` | `fpga/report/` | 综合实现原始报告 + 资源时序表 + 2018.3 变更记录 |
| `host/app/` | `host/app/` | `vc_stream.cpp` + 流式/INT8 模块 + third_party + 构建脚本 |
| `host/model/` | `host/model/` | 权重 blob + `MODEL.md`（来源、结构、SHA） |
| `host/deploy/` | `host/deploy/` | 串口上传/回读/上板运行/PL 加载/板端 C 工具 + 预编译二进制 |
| `metrics/metrics.csv` | `metrics/metrics.csv` | 130 行汇总（每行带 source/硬件/次数/时长，source 为包内相对路径） |
| `metrics/logs/` | `metrics/logs/` | `board_c/`（22 个）、`stability_20261026/`（8 个）、`o64_live_20261027/`（15 个）、`pl_build/`（19 个），未编辑 |
| `metrics/reports/` | `metrics/reports/` | `metrics.csv` 引用的 6 份分析报告（原样拷贝，含 SHA），补上溯源链 |
| `metrics/scripts/` | `metrics/scripts/` | 评分器、逐阶段比对、板端输出校验、延迟分布采集 |
| `metrics/evidence/` | `metrics/evidence/` | 语谱图对照、波形总览 |
| `report/` | `report/` | 设计报告 + 失败分析 + 提交自查表（`SUBMISSION_CHECKLIST_FINAL.md`） |
| `ai_collaboration/` | `ai_collaboration/` | 6 组专题 + 28 轮索引 + 原始日志附录 |
| （加分项）`skill/` | `skill/` | 3 个 skill，均含"换题目/换板卡怎么用" |

**额外补充**（官方未要求但对复现有用）：
`docs/toolchain.md`（2018.3 合规与构建命令）、`metrics/inputs/`（固定测试输入）、
`metrics/reports/`（被引用的源报告，原样拷贝）、`metrics/resource_timing.csv`（自动抽取的资源时序）、
`fpga/src/README.md`、各子目录的 `README.md`。

> 全部目录名与文件名均为**纯英文**（ASCII 可见字符）；中文只出现在正文。
> 例外只有两类：官方模板要求的 `README.md` 大写，以及 `host/app/third_party/` 下
> 必须与上游保持一致的 `AAFilter.cpp`、`LICENSE.txt`、`Makefile` 等文件名
> （改名会破坏 `#include` 与 LGPL 归属，见 `metrics/README.md` §8）。

---

## 3. 从零复现

### 3.0 你需要

| 项 | 要求 |
|---|---|
| 板卡 | Zynq-7020（本项目用野火皓月 `xc7z020clg400-2`），已烧 PetaLinux 2022.2 或等价镜像 |
| 主机 | Windows + Vivado/SDK **2018.3**（或 2025.2/2026.1 自行验证 IP 版本，见 `docs/toolchain.md`） |
| 串口 | USB-UART 到板子，主机侧确认端口号（本项目为 COM8） |
| Python | 3.10+；跑评价指标需 torch / pyworld 0.3.5 / librosa（`metrics/scripts/`） |
| 可选 | 麦克风（3.5 mm 粉色口）+ 耳机/音箱（绿色口） |

> **测试输入**：`metrics/inputs/` 下有 4 s 的固定测试片段（`test_src_16k.wav` / `test_src_32k_s24.raw`），
> 它来自**真人源语音**，因此**不放进提交压缩包**（见 `MANIFEST.md` §4）；本目录里保留一份供内部复核。
> 拿不到它时，§3.2/§3.4 用**任意 4 s、32 kHz、S24_LE、双声道**的输入替代即可，
> 判据（`ok:true`、`samples_out == samples_in`、0 欠载）不变。

### 3.1 只看结果（最快，5 分钟）

```powershell
# 1) 资源/时序从原始报告重新抽取（当前入链的 STFT 版），核对是否与报告一致
python skill\golden_reference_compare\collect_metrics.py --vivado-dir fpga\stft\report `
    --out metrics\resource_timing_stft_check.csv --md metrics\resource_timing_stft_check.md
#    期望：16,723 LUT / 28,677 FF / 22 BRAM / 76 DSP；WNS +0.347 / WHS +0.040 ns
#    备用变调核换成 --vivado-dir fpga\report（期望 8,378 LUT / 5 BRAM / 6 DSP、WNS +0.813 ns）

# 2) 跑比对工具的回归测试（不需要板卡）
python skill\golden_reference_compare\example\gen_demo.py     # 期望 DEMO PASS

# 3) 读报告
start report\design_report.md
start metrics\summary.md
```

> 第 1 步的完整版（含两份遥测，可逐字节复现 `metrics/resource_timing.csv` 的 51 行）
> 见 `metrics/README.md` §4。

### 3.2 重建 PS 程序（10 分钟）

```powershell
# 交叉编译（板上运行）
cd host\app
.\build_arm.ps1            # 产物 build\vc_stream_arm，脚本自动校验 ELF 头与 SHA

# 主机侧同源码（数值迭代用）
.\build_host.ps1           # 产物 build\vc_stream_host.exe
```

自检（不需要板卡；**先回到包根目录**，上面的 `cd host\app` 还在生效）：

```powershell
cd D:\competition_pkg_20261026     # 包根（换成你解压到的位置）
$py = "python"     # 需要 numpy；原工程用的是 env\venv\Scripts\python.exe
& $py -c "print('ok')"

cmd /c "host\app\build\vc_stream_host.exe 4 native_s24 200 --model host\model\student_v5.blob < metrics\inputs\test_src_32k_s24.raw > %TEMP%\out.raw 2> %TEMP%\tel.json"
type $env:TEMP\tel.json       # 期望 ok:true，samples_out == samples_in
```

### 3.3 重建 PL 位流（15–25 分钟，可选）

```powershell
fpga\build\build_pl.ps1 -Work D:\pl_try
# 资源/时序应复现；位流 SHA 会不同（布线不可位复现），这是正常的
```

如果不想重建，直接用在板的镜像：`fpga\build\audio_pitch_dma_2018_swap.bin`。

### 3.4 上板（30 分钟，其中 10 分钟在等串口）

```powershell
# 0) 关掉所有串口终端（COM8 独占）
# 1) 组装脚本期望的目录布局
.\host\deploy\stage.ps1
# 2) 一键：preflight → 上传 → 跑 4 s 主链 + 对照 → 回读
.\host\deploy\deploy_all.ps1
# 或者逐步（更可控）
cd D:\vc_stage_20261026
.\tools\board_preflight.ps1
.\tools\board_upload_all.ps1
.\tools\board_run.ps1
.\tools\board_download_results.ps1
```

板端手动跑一次（确认"真的在跑"）：

```sh
cd /tmp/vc
./vc_stream 4 native_s24 200 < in.raw > out.raw 2> tel.json
tail -1 tel.json        # 看 rtf / clipped_samples

# 实时演示（300 ms 块；端到端 p95 576.7 ms，30 min 实测 0 欠载）
cat in.raw in.raw in.raw | ./vc_stream 12 native_s24 200 --stream 300 --preset live \
  | aplay -D default -t raw -f S24_LE -r 32000 -c 2 --start-delay=64000
```

### 3.5 上 PL（可选，验证 bit-exact）

```powershell
.\host\deploy\stage.ps1          # 已包含位流与 regtool
# 按 host\deploy\README.md §4 传位流与工具，然后板上：
cd /tmp/pl_2018
gunzip -c audio_pitch_dma_2018_swap.bin.gz > audio_pitch_dma_2018_swap.bin
python3 prepare_recovery.py /tmp/pl_2018
python3 load_pl_2018.py /tmp/pl_2018 /tmp/pl_2018/audio_pitch_dma_2018_swap.bin
./regtool --base 0x41200000 --check 0x00:18:86856,65536,131072,32768,86856 --check 0x08:1:0,1
./pitch_dma_mem input_s24_stereo.raw out.raw 86856 s24     # 期望 4.10 M 样本/s
```

主机比对（先把板端回读的两个 dump 放到同一目录；期望 `max_abs_diff 0`）：

```bash
python fpga/src/compare_reference.py <回读目录>/input16_mono.raw <回读目录>/output16.raw 86856
```

### 3.6 复算四指标（10 分钟 + 模型加载）

```powershell
$py = "python"      # 需 numpy / soundfile / torch / whisper / UTMOS 资产（见 §3.0）
# 需要一份 4 s 的转换结果 wav；本包只带 4 s 的原始输入
& $py metrics\scripts\score_full.py <你的输出.wav> --cer-from metrics\inputs\test_src_16k.wav
```

> `score_full.py` 依次找两份**不随包分发**的东西：
> ① 评测权重（WeSpeaker ResNet34 / UTMOS22-Strong / whisper-small）——默认找
> `<包>/metrics/assets/evaluator_assets`，可用环境变量 `FVC_ASSETS` 指到别处；
> ② 目标女声/男性语料 `metrics/data/pair16k/manifest.json`（含真人语音，**不随包分发**）。
> 缺任一项都会在加载期报 `FileNotFoundError` 并打印所找路径，不会"静默算出一个错数"。
> 要复算四指标需自备同一份语料，否则只能核对 `metrics/logs/board_c/scores_*.json`
> 里的既有结果。这一点是复现的**已知限制**，写在 `metrics/README.md` §3。

---

## 4. 关键结果速览

详细表格见 [`metrics/summary.md`](metrics/summary.md) 与
[`report/design_report.md`](report/design_report.md) §6。

| 类别 | 最好的数字 | 出处 |
|---|---|---|
| RTF（4 s 批处理，默认档） | **0.972** | `metrics/logs/board_c/board_final_telemetry.json` 同源 |
| RTF（live 档） | **0.845** | `board_c_20261025_squeeze.md` |
| 端到端延迟 | **576.7 ms（p95）**（300 ms 块，live 档） | `metrics/STABILITY_20261026.md` |
| PL 变调核吞吐（备用） | **4.10 M 样本/s**，RTF 0.0078 | `pl_build_20261025.md` §4 |
| PL bit-exact（备用变调核） | **128000/128000**，三个比例 | `fpga/report/m3_compare_*.txt` |
| **PL STFT 段** | **449.04 → 305.82 ms**（−31.9%，含 DMA 75.63 ms）；整链 **RTF 0.9376 → 0.9019** | `fpga/stft/PL_STFT_20261027.md` §5 |
| **PL STFT 一致性** | **corr 0.99999999 / max 4 LSB / rms 0.60 LSB** | 同上 |
| **PL STFT 资源/时序** | **16,723 LUT / 22 BRAM / 76 DSP，WNS +0.347 ns** | `fpga/stft/report/impl_*.txt` |
| C↔Python | **121.71 dB / 126.16 dB** | `board_c_20261025.md` §8.2 |
| O64 上板（整段 23.72 s，精确档） | identity **0.7293** / UTMOS **2.2659**（电脑端 0.7195 / 2.2681） | `report/o64_onboard_20261026.md` |
| **O64 + live（演示档）** | RTF **0.860**、60 s **0 欠载**、p99 **284.8 ms**；identity **0.7321** / UTMOS **2.1900** | `metrics/O64_LIVE_20261027.md` |
| **O64 + live + PL STFT（联测）** | RTF **0.8237**、60 s **0 欠载**、处理 p99 **274.8 ms**、端到端 574.8 ms；STFT 段 **451.3→309.5 ms**；identity **0.7324** / UTMOS **2.1532** | `report/PL_IN_LOOP_20261027.md` |
| O64 板端 vs Python O64 参考 | corr **0.999999987** / SNR **75.71 dB** | 同上 |
| ARM↔x86 | **139.38 dB** | `board_c_20261025.md` §8.2 |
| 资源（STFT 版） | 16,723 LUT / 28,677 FF / 22 BRAM / 76 DSP | `fpga/stft/report/impl_utilization.txt` |
| 时序（STFT 版） | WNS **+0.347 ns**，0 failing endpoints | `fpga/stft/report/impl_timing.txt` |

---

## 5. 已知缺口（一句话版）

1. **PL 与主链的集成：已解决（2026-10-27）**——PL 承担 STFT/IFFT + 频域乘法（corr 0.99999999 / 4 LSB，
   STFT 段 449→306 ms）。变调核保留为**已验证的备用设计**，与 STFT 版互斥、不能同时加载。
2. **UTMOS < 2.30**：精确档 2.2659（差 0.034）、live 档 2.1900（差 0.110）——算法天花板，非实现问题；
   泄漏已由 O64 解决（精确档 −0.0223 / live 档 −0.0346）。
   **换建模方式的第一步也试过**：GAN 声码器支线（F13）把 identity 追平到 0.726、周期度 0.856，
   但 UTMOS 只到 1.368，决定性证据是"换 T4 相位 +0.50、换 T4 幅度只 +0.04"——卡在声门相位谱，
   该支线**未入包**（`report/failure_analysis.md` F13）。
3. **人工盲测未做**；p50/p95/p99 与 30 min 长稳已于 2026-10-26 补测，
   见 `metrics/STABILITY_20261026.md`。流式路径有 0.019% 样本削波（批处理为 0），
   已在同文件 §5 写明。
4. **四指标复算需要目标语料**（含真人语音，不随包分发）。
5. **演示定版 = O64 + live + PL STFT**（RTF **0.8237**、60 s 0 欠载、处理 p99 **274.8 ms**、
   STFT 段 451.3→309.5 ms；identity **0.7324** / UTMOS **2.1532**），
   质量上限仍按精确档报（0.7293 / 2.2659，RTF 1.345 只能批处理）。
   PL STFT 与 live 档**已联测**（2026-10-27），见 `report/PL_IN_LOOP_20261027.md`；
   注意旧 `vc_o64_pl`(04:25) 与 v5 位流不兼容，不可用于取数。

详见 [`report/failure_analysis.md`](report/failure_analysis.md) §4。

---

## 6. 赛事要求逐条对照

| 要求 | 本包 | 位置 |
|---|---|---|
| 初级组器件（Zynq-7000） | `xc7z020clg400-2` | `docs/hardware_setup.md` |
| 实现方式（RTL/PS 任意组合） | PS C 主链 + RTL：PL 承担 STFT/IFFT + 逐 bin 频域乘法（变调核为备用） | `docs/architecture.md`、`fpga/stft/` |
| 工具版本（2026.1/2025.2，其它须说明并保证可复现） | 2018.3，**已说明 + Tcl 全入库 + 原始报告** | `docs/toolchain.md` |
| 板上跑通 + 实测输出 | 4 s / 23.72 s O64 / 30 min 实测、日志与 SHA 齐全 | `metrics/logs/` |
| **大模型协作记录**（提示词/回答/自我纠错） | 6 组专题 + 28 轮索引 + 94 KB 原始摘要 | `ai_collaboration/` |
| **协作经验提炼为技能包** | 3 个 skill（通用性高、含复用场景） | `skill/` |
| 加分项：通用 Overlay 加载与寄存器范式 | `overlay_load_and_verify` | `skill/` |
| 加分项：DMA 搬运与缓存一致性封装 + 出错定位 | `dma_cache_coherency`（含 6 类故障判读表） | `skill/` |
| 加分项：黄金参考比对 + 性能资源自动采集 | `golden_reference_compare`（含 `collect_metrics.py`） | `skill/` |
| 加分项：从接口契约生成主机侧代码/测试骨架 | `docs/interface.md` + `regtool` 的寄存器表驱动（部分覆盖） | `skill/overlay_load_and_verify` |
| 考察：功能正确、实测、数据真实完整、他人能复现 | 见 `report/`、`metrics/` | — |
| 考察：创新性与应用价值 | 单列见 `report/design_report.md` §7 | — |
| 目录/文件名纯英文 | 全部英文，中文只在正文 | — |

---

## 7. 许可与致谢

- **WORLD** 4.2（`third_party/world/`）：Modified BSD，见 `LICENSE.txt`。
- **SoundTouch** 2.x（`third_party/soundtouch/`）：LGPL 2.1，见 `COPYING.TXT`。
  本项目**静态链接**它；如需再分发二进制，请注意 LGPL 的相应义务。
- 权重 blob 为本团队自训练产物（见 `host/model/MODEL.md` §7）。
- **真人语音**：目标女声/男性语料不随本包分发；本目录里唯一的真人源片段是
  `metrics/inputs/` 的 4 s 测试向量，**已从提交用压缩包中剔除**（`MANIFEST.md` §4 列明）。
  `metrics/logs/` 里的 `.wav`/`.f32` 是本系统的**输出**（用于复算指标的证据），不属源录音。
