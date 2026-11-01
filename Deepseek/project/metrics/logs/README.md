# logs — 原始日志（未编辑）

原则：**报告里的每个数字都应该能在这里找到原始出处**。日志一律原样拷贝，不改格式、不删行，
失败的日志也保留。

---

## 1. `board_c/` — PS 侧（板上运行）

| 文件 | 内容 |
|---|---|
| `board_final_telemetry.json` | **stage-1 的完整分阶段耗时**（`total_ms 8268.88`、`rtf 2.0672`、`mlp_ms 3817`、`d4c_ms 1470`…） |
| `board_nopitch_telemetry.json` | 同上的 `--nopitch` 对照（`rtf 1.8074`，峰值 1.5666，削波 391） |
| `board_run_20261025_204541.log` | 一次完整的板上会话（命令 + 输出 + 校验） |
| `preflight_20261025_203115.log` | 上板前置：系统/声卡/PL 状态 |
| `upload_20261025_203129.log` | 串口上传（二进制 + 权重 + 输入，逐文件 SHA） |
| `download_20261025_*.log` | 三次回读（输出 + 三个中间量 dump） |
| `build_arm.log` | 交叉编译日志（含 ELF 头校验与 SHA） |
| `build_host.log` | 主机构建日志（0 字节：构建无输出即成功） |
| `scores.json` / `scores_cer.json` / `scores_int8.json` / `scores_L5.json` | 四指标原始输出（含 `hyp` 转写文本与各门禁 pass/fail） |
| `manifest.json` | 参与打分的 wav 清单与 SHA |
| `o64_*.json` / `o64_board_full_y16.f32` | 2026-10-26 的 O64（64 阶）上板证据：板端遥测、与 Python 参考的 SNR、逐阶段误差、四指标原始输出 |

**引用示例**：报告里 `total_ms 8268.88` → `board_final_telemetry.json`；
`UTMOS 2.1045` → `scores_cer.json`；`CER 0.0769 / hyp` → 同文件。

## 2. `pl_build/` — PL 侧（构建 + 上板）

| 文件 | 内容 |
|---|---|
| `create_2018_3.log` | 首次建 BD（无 GPIO）→ `AUDIO_PITCH_DMA_VALIDATED` |
| `create2_2018_3.log` | **失败**：GPIO 的 `s_axi_aclk` 未接 → `[BD 41-758]`（保留为证据） |
| `create3_2018_3.log` | 补时钟后通过 |
| `synth_2018_3.log` / `synth2_2018_3.log` | 综合（前者是首跑，后者是最终） |
| `impl_2018_3.log` | 实现 + 位流（180 KB） |
| `export_hdf.log` | `write_hwdef` + `write_sysdef` → `.hdf` |
| `board_recovery_prep_20261025.log` | 从启动分区生成回滚镜像（只读） |
| `board_gunzip_bitstream_20261025.log` | 板上解压位流 + SHA 核对 |
| `board_pl_load_20261025.log` | 加载全过程：记录状态 → unbind 18 个消费者 → 写 firmware → rebind 音频 |
| `board_gpio_check_20261025.log` / `board_gpio_check2_20261025.log` | AXI GPIO 写读校验（含首次失败） |
| `board_m3_dma_20261025.log` | DMA 端到端跑数（吞吐、chunk 时间、SHA） |
| `board_reload_rerun_20261025.log` | 重新加载位流后重跑（获得"从零状态"） |
| `board_ratio_identity_20261025.log` | `ratio=65536` 恒等测试（输出 SHA == 输入 SHA） |
| `board_ratio48k_clean_20261025.log` | `ratio=48000` 的第二次 bit-exact 复验 |
| `board_stage_prep_20261025.log` | 阶段准备（文件摆放/校验） |
| `board_final_state_20261025.log` | 撤离前快照（fpga 状态、PCM 状态、内存、两个镜像 SHA） |
| `upload_m2m3_20261025.log` | 位流与工具的上传记录 |

> `board_recovery_prep_20261025.log` 里的回滚镜像 SHA `af275946…` 与 2026-10-10 的历史记录一致，
> 这是"原厂位流未变 + 交换算法未变"的证据。

## 3. `stability_20261026/` — 延迟分布 + 30 min 长稳（2026-10-26 新补）

| 文件 | 内容 |
|---|---|
| `lat_300_fix.csv` | 60 s / 300 ms 块的 p50/p95/p99/max（修正版 `measure_latency.sh` 产出） |
| `lat_300_blocks_fixed.jsonl` | 该轮 200 块的逐块 JSON（`proc_ms` 为**累计**值，取差分即每块） |
| `lat_300_blocks_raw.jsonl` | 修正前那一轮（用来说明"累计值当分位数"的 bug，p50=26 s） |
| `blocks.jsonl` | 30 min 长稳 6000 块的逐块 JSON + 末尾 summary（`clipped_samples` 在这里） |
| `aplay.log` | aplay 全部输出（78 B，无 underrun） |
| `mem.csv` | 每 30 s 的 vc_live RSS / 系统空闲内存 / 已完成块数 |
| `env.txt` | 硬件、内核、CPU 频率、FPGA 状态、二进制与输入 SHA |
| `analysis.json` | 上面这些的机器可读汇总（分位数、underrun、RSS 变化、块连续性） |

## 4. 对应的文本报告（不在本目录，在 `fpga/report/`）

| 文件 | 内容 |
|---|---|
| `m3_compare_clean.txt` | **PASS**：128000 样本 `max_abs_diff 0` |
| `m3_compare_output.txt` | **FAIL**：16 个样本错（2×8 全 0）——缓存脏行回写的原始证据 |
| `m3_compare_ratio48k.txt` | 第二个比例的 PASS |
| `synth_*.txt` / `impl_*.txt` | 资源、时序、DRC、bus skew、时钟 |

> 上面三个 `m3_compare_*.txt` 是板端 C 工具在 Windows 控制台上重定向出来的，
> 编码是 **UTF-16LE（带 BOM）**，不是 UTF-8。这是原样保留的原始输出，没有转码——
> 转码就等于改了证据。PowerShell 的 `Get-Content` 能直接读；
> 用 `grep`/`rg` 时加 `--text` 或先 `Get-Content ... | Set-Content -Encoding utf8` 转一份副本再看。
> 其余所有 `.txt` 都是 UTF-8。

## 5. 怎么用这些日志

```bash
# 找某个数字的出处
grep -r "8268" metrics/logs/
grep -r "max_abs_diff" fpga/report/

# 核对第四位小数的来源
grep -n "utmos" metrics/logs/board_c/scores_cer.json
```

## 6. 没有保留的日志（诚实说明）

- 板上 `/tmp` 是 tmpfs，**重启即失**。2026-10-25 那轮 12 s 流式跑没有把逐块 JSON 回读到主机，
  所以当时 p50/p95/p99 缺失；**2026-10-26 已补测并回读**，见
  `stability_20261026/`（`lat_300_blocks_fixed.jsonl` 60 s 逐块、`blocks.jsonl` 30 min 逐块）。
- 早期（2026-10-09~10-21）的完整会话日志在另一个工作目录，本包只保留了
  `ai_collaboration/appendix_ai_worklog.md` 的逐日摘要。
