# MANIFEST — 参赛包清单

> 本文件由脚本对目录做全量扫描生成（**统计不含本文件自身**）。
> 包根：`D:\competition_pkg_20261026\`；生成日：2026-10-27（Asia/Shanghai）。
> 提交用压缩包见 §4（与本目录的差异**只有**被剔除的真人源录音）。

## 1. 总量

| 项 | 值 |
|---|---|
| 文件总数 | **345**（含本文件 346） |
| 总大小 | **52,134,319 B（49.72 MiB）** |
| 目录总数 | 58 |
| 最大单文件 | `host/model/student_v5_o64.blob`（4,941,804 B） |
| 超过 100 MB 的文件 | **0 个** |

文件类型分布（按扩展名，前 12）：

| 扩展名 | 文件数 |
|---|---:|
| `.md` | 55 |
| `.h` | 31 |
| `.json` | 31 |
| `.py` | 30 |
| `.log` | 29 |
| `.txt` | 28 |
| `.tcl` | 21 |
| `.cpp` | 20 |
| `.ps1` | 18 |
| `.c` | 12 |
| `<none>` | 9 |
| `.v` | 8 |

## 2. 各目录文件数

| 目录 | 文件数 | 大小 |
|---|---:|---:|
| `ai_collaboration/` | 9 | 135,392 B（0.13 MiB） |
| `docs/` | 4 | 35,713 B（0.03 MiB） |
| `fpga/` | 111 | 29,183,924 B（27.83 MiB） |
| `host/` | 85 | 13,001,459 B（12.40 MiB） |
| `metrics/` | 97 | 7,529,529 B（7.18 MiB） |
| `report/` | 11 | 1,095,531 B（1.04 MiB） |
| `skill/` | 27 | 1,135,548 B（1.08 MiB） |
| `<root>/`（根目录文件） | 1 | 17,223 B（0.02 MiB） |
| **合计** | **345** | **52,134,319 B（49.72 MiB）** |

### 2.1 `fpga/` 细分

| 子目录 | 文件数 | 大小 |
|---|---:|---:|
| `build/` | 9 | 13,749,024 B（13.11 MiB） |
| `report/` | 16 | 717,296 B（0.68 MiB） |
| `src/` | 15 | 57,950 B（0.06 MiB） |
| `stft/` | 71 | 14,659,654 B（13.98 MiB） |

### 2.2 `host/` 细分

| 子目录 | 文件数 | 大小 |
|---|---:|---:|
| `app/` | 62 | 2,138,191 B（2.04 MiB） |
| `deploy/` | 18 | 1,073,534 B（1.02 MiB） |
| `model/` | 5 | 9,789,734 B（9.34 MiB） |

### 2.3 `metrics/` 细分

| 子目录 | 文件数 | 大小 |
|---|---:|---:|
| `evidence/` | 3 | 1,538,764 B（1.47 MiB） |
| `inputs/` | 2 | 1,152,044 B（1.10 MiB） |
| `logs/` | 65 | 4,592,620 B（4.38 MiB） |
| `reports/` | 7 | 122,368 B（0.12 MiB） |
| `scripts/` | 13 | 54,469 B（0.05 MiB） |
| `<files>` | 7 | 69,264 B（0.07 MiB） |

### 2.4 `skill/` 细分

| 子目录 | 文件数 | 大小 |
|---|---:|---:|
| `dma_cache_coherency/` | 8 | 550,826 B（0.53 MiB） |
| `golden_reference_compare/` | 9 | 37,245 B（0.04 MiB） |
| `overlay_load_and_verify/` | 9 | 543,647 B（0.52 MiB） |
| `<files>` | 1 | 3,830 B（0.00 MiB） |

## 3. 关键产物 SHA256

校验方式：`Get-FileHash <file> -Algorithm SHA256`（或 `sha256sum`）。

| 文件 | 字节 | SHA256（前 32 位） |
|---|---:|---|
| `fpga/stft/bitstream/stft_dma.bit` | 4,045,672 | `346e40c2a962069e7eed9f0a34c360bd…` |
| `fpga/stft/bitstream/stft_dma.bin` | 4,045,564 | `89d6f0c127b9322e4ab239ac10ece532…` |
| `fpga/stft/bitstream/stft_dma_swap.bin` | 4,045,564 | `d597cb0af256e4b62b44b26a511696e5…` |
| `fpga/stft/bitstream/stft_dma_swap.bin.gz` | 568,326 | `da1701f28b3e6c482e9d728187c708c4…` |
| `fpga/stft/bitstream/stft_dma.hwdef` | 443,125 | `db9079d5af268ca8c8d19c441453db88…` |
| `fpga/stft/bitstream/vc_o64_pl` | 812,624 | `13d48df76a6366a54dce22bd4652ac50…` |
| `fpga/build/audio_pitch.bit` | 4,045,672 | `406667b4657e3623c15da8265a61b6f0…` |
| `fpga/build/audio_pitch.bin` | 4,045,564 | `ce1552c9e4b5559fc111d4c6f1a400a5…` |
| `fpga/build/audio_pitch_dma_2018_swap.bin` | 4,045,564 | `8aedb87d4144dd744e618258a5cddc26…` |
| `fpga/build/audio_pitch_dma_2018_swap.bin.gz` | 332,294 | `faf6c27130bb594a8bbac121e06d1e5e…` |
| `fpga/build/audio_pitch.hdf` | 827,497 | `2545a57e95ed60b4d2b5e3b0d82bd0cf…` |
| `host/model/student_v5_o64.blob` | 4,941,804 | `01aecb78d4a5a9b1a960f4a15cbc4bc5…` |
| `host/model/student_v5.blob` | 4,843,308 | `c04107b95de35fb3f08125274099c583…` |
| `host/app/build/vc_stream_arm` | 804,424 | `557cc08a67fadc6e452733c15eb4adb8…` |
| `host/app/build/vc_stream_o64_arm` | 804,424 | `1a9ca16d338d5bb5625667ba9bb05a40…` |
| `host/deploy/bin/pitch_dma_mem` | 512,328 | `fe312bb177a02011864e5548c5272b01…` |
| `host/deploy/bin/gpio_check` | 506,636 | `512ae05c0e9e211e71f8d7ee6b2b11ff…` |
| `skill/dma_cache_coherency/bin/dma_roundtrip` | 511,928 | `fa20a4e2f8832fff3ce5d730b12b4905…` |
| `skill/overlay_load_and_verify/bin/regtool` | 506,720 | `083a59bf41cd07b4c9fad4a1c147aaf7…` |
| `fpga/stft/rtl/axis_stft_gain.v` | 15,765 | `eec4cfc08ac31bf3c6c60ebccc66ac6a…` |
| `host/app/src/vc_stream.cpp` | 71,874 | `adff703cadadfc339c0e22d8dccdbcae…` |
| `metrics/metrics.csv` | 23,079 | `dd89d8b9c54ae6134ca69a2bd95c531c…` |
| `metrics/resource_timing.csv` | 3,100 | `b4ac5818be370efe5c2db74ef8bcd55d…` |
| `metrics/summary.md` | 15,316 | `ccec37426ca7526e22a025638037c050…` |
| `report/design_report.md` | 32,257 | `ee33b8132f688a1541756b3c319453b7…` |
| `report/failure_analysis.md` | 15,030 | `658915cf31efa4193cc8f108bed22ac5…` |
| `metrics/reports/board_c_20261025.md` | 27,768 | `a88754f62b41e43f92a4963a140be768…` |
| `metrics/O64_LIVE_20261027.md` | 8,773 | `8220610dc4ffa140b5753b297618434b…` |
| `docs/toolchain.md` | 10,521 | `ecf275822b0dc29e28768f7b8ea8cbd2…` |

完整校验清单（不截断）：`fpga/build/SHA256SUMS.txt`、`fpga/stft/SHA256SUMS.txt`、
`metrics/reports/README.md`（6 份源报告）。

## 4. 提交压缩包与排除项

| 项 | 值 |
|---|---|
| 压缩包 | `D:\competition_submit_20261027.rar`（RAR5，`a -r -m5 -ep1 -idq`） |
| 内容根目录 | 与本包一一对应，**340** 个文件（342 − 2 个真人源录音） |
| 条目布局 | `-ep1` 去掉顶层目录名：解压后 `README.md`、`report/`、`host/` … 直接展开；要还原成 `competition_pkg_20261026/` 就解压到同名目录 |
| 压缩后体积 | 约 **20 MiB**（RAR5 `-m5`；BIN/位流压缩率约 2.4×） |
| 条目命名 | 全部正斜杠 `/`、无中文、无重名（Unix 工具可直接解压） |
| 剔除单文件 >100 MB | **无**（最大 4.94 MB） |
| 剔除真人音频 | **2 个**（见下表） |

被剔除的真人源录音（**只从压缩包剔除，包目录内仍保留**）：

| 文件 | 字节 | 理由 |
|---|---:|---|
| `metrics/inputs/test_src_16k.wav` | 128,044 | 来自真人男声（male_04）的 4 s 固定测试向量 |
| `metrics/inputs/test_src_32k_s24.raw` | 1,024,000 | 同上，32 kHz S24 双声道版本 |

> 剔除后压缩包内仍可完成：资源/时序重抽取（README §3.1）、比对工具回归测试、
> PS 程序重建、PL 位流重建、报告与全部指标/日志核对。
> **不能**直接完成的两步是 README §3.2/§3.4 的板级自检与 §3.6 的四指标复算——
> 前者可用任意 4 s/32 kHz/S24 输入替代，后者本来就需自备目标语料（见 `metrics/README.md` §3）。

## 5. 与官方要求目录的对照

| 要求 | 是否齐备 | 位置 |
|---|---|---|
| README | ✔ | `README.md` |
| docs | ✔ | `docs/`（architecture / hardware_setup / interface / toolchain） |
| fpga/src | ✔ | `fpga/src/`（rtl / bd / constraints）+ `fpga/stft/`（当前入链） |
| fpga/build | ✔ | `fpga/build/`（.bit/.bin/.hdf/swap/SHA256SUMS/build_pl.ps1） |
| fpga/report | ✔ | `fpga/report/` + `fpga/stft/report/`（原始综合实现报告） |
| host | ✔ | `host/app/` + `host/model/` + `host/deploy/` |
| metrics | ✔ | `metrics.csv` + `logs/` + `scripts/` + `evidence/` + `inputs/` + `reports/` |
| skill | ✔ | `skill/`（3 个，各含 README + results） |
| ai_collaboration | ✔ | `ai_collaboration/`（6 专题 + 28 轮索引 + 94 KB 附录） |
| report | ✔ | `report/`（设计报告 / 失败分析 / 提交自查表） |

