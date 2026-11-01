# metrics 缺口补齐：延迟分布 + 30 min 长稳（2026-10-26）

## 0. 结论

| 项 | 结果 | 判定 |
|---|---|---|
| 延迟分布（300 ms 块，60 s，200 块） | **p50 268.70 / p95 276.70 / p99 277.90 / max 278.10 ms** | 补齐 `not_measured` ✅ |
| 端到端（+300 ms 块） | p50 **568.70** / p95 **576.70** / p99 **577.90** / max **578.10 ms** | e2e p95 ≤ 700 ms ✅ |
| 30 min 长稳 | 6000/6000 块、1800.0 s 音频、**underrun 0**、无掉块、rtf 0.9963 | ✅ |
| 削波 | **21 473 个样本**（115.2 M 输出的 0.019%） | ⚠️ 非 0，见 §5 |
| 内存 | RSS **8 172 KB 恒定**（t=30 s → t=1770 s，Δ=0）；空闲内存 694 360 → 693 468 KB | 无泄漏 ✅ |
| 是否掉音 | 无：block 序号 1..6000 连续，aplay 无 underrun、无 error/broken pipe | ✅ |

## 1. 环境（测试记录）

| 项 | 值 |
|---|---|
| 硬件 | Embedfire ZYNQ Board（野火皓月 Zynq-7020，`xc7z020clg400-2`） |
| 板端系统 | 内核 `5.15.0-xilinx`，armv7l；`/etc/version` 20180309123456 |
| CPU | 666.667 MHz（governor `userspace`） |
| FPGA | `fpga_manager/fpga0/state = operating`；**PL 未加载/未改动**（仍是变调核位流，本任务不用它） |
| 串口 | COM8 / 115200 / 8N1 / root；用时确认无其它进程占用 |
| 二进制 | `/tmp/vc/vc_live`，804 424 B，sha256 `83257578…`（与 `board_c_20261025_squeeze.md` 记录的 L5 档一致） |
| 权重 | `/tmp/vc/student_v5.blob`（T4/48 阶，4 843 308 B） |
| 输入 | `/tmp/vc/in.raw`，32 kHz S24 立体声 4 s（sha256 `96dd7752…`），循环喂入 |
| 块长/档位 | 300 ms，`--preset live`（ct_stride 2 + sm_stride 2 + int8），`out_gain 0.6`，`--start-delay=64000` |
| 演示服务 | 测试前 `/etc/init.d/world-voice stop`，测试后保持 stop |

## 2. 延迟分布（`measure_latency.sh`，60 s，300 ms 块）

```
block_ms,blocks,proc_min_ms,proc_p50_ms,proc_p95_ms,proc_p99_ms,proc_max_ms,proc_mean_ms,e2e_p50_ms,e2e_p95_ms,e2e_p99_ms
300,200,233.00,268.70,276.70,277.90,278.10,259.34,568.70,576.70,577.90
```

- 这一轮 `stdout` 接 `/dev/null`，量的是**纯处理时间**（脚本头部定义），不含 aplay 调度。
- 200 块全部 ≤ 278.2 ms：**每块余量 ≥ 21.9 ms**（p50），p95 余量 23.3 ms。
- 与旧记录 285 ms/块（12 s ×3）差 16 ms，是因为旧记录是 aplay 链路里的均值（含写管道阻塞），
  纯处理更快；两者不矛盾，但**引用时必须说明口径**。

### 2.1 脚本自身的一个 bug（已修）

原 `measure_latency.sh` 第一次跑出来是 `p50 26 095.9 ms / p99 51 515.5 ms`——
它把 `vc_live` 打印的**累计** `proc_ms` 当成了每块耗时（`stream_mode.inc:215` 是
`st.proc_ms += …`）。修正版对累计值取一阶差分，并加了"差分和 == summary 总和"的自检
（51 867.20 vs 51 867.18 ms）。原文件保留为 `scripts/measure_latency.sh.orig`，
详细说明见 `scripts/CHANGES_measure_latency_20261026.md`。

## 3. 30 min 长稳（`stab30.sh`，aplay 链路）

链路：`(循环 cat in.raw) → vc_live 1800 native_s24 200 --stream 300 --preset live → aplay -D default …`

| 指标 | 值 |
|---|---|
| 音频时长 | 1800.0 s（6000 块 × 300 ms） |
| 实际墙钟 | 1799.8 s（rtf 0.9963） |
| underrun | **0**（`aplay.log` 只有一行 "Playing raw data…"，全文 78 B） |
| 掉块 | 0（block 序号 1..6000 连续，无重复/跳跃） |
| 削波 | 21 473 样本 / 115 200 000（0.019%） |
| 平均每块 | 298.9 ms（300 ms 预算 → 余量 1.1 ms/块，靠 aplay 2 s 缓冲吸收抖动） |
| 每块分布（aplay 链路） | p50 275.4 / p95 373.9 / p99 373.9 / max 374.2 ms |
| 内存 | RSS 8 172 KB 恒定；空闲 694 360 → 693 468 kB（−892 kB，正常波动） |

### 3.1 为什么 aplay 链路的每块分布是双峰的

`proc_ms` 的计时点包含 `fwrite/fflush(stdout)`（`stream_mode.inc:211-215`）。
接 aplay 时管道会满，写阻塞被计进"处理时间"，于是呈现 **~250 ms / ~370 ms 两簇**
（直方图：240–260 ms 1193 块、260–275 ms 1665 块、320–360 ms 1357 块、360–380 ms 875 块）。
所以：

- **纯处理分布**看第 2 节（268.7 / 276.7 / 277.9 / 278.1）；
- **能不能实时**看本节（均值 298.9 < 300，30 min 0 欠载）。

两个口径都写进 `metrics.csv`，不混用。

## 4. 内存

`mem.csv` 每 30 s 采一次，60 个采样点：

- t=0：5 736 kB（模型 blob 4.8 MB 还没被真正读进来）
- t=30 s 起：8 172 kB，此后 **29.5 分钟一次没变**
- 瞬时峰值 8 960 kB（t=120–150 s，页缓存/工作集），之后回落到 8 172 kB
- 系统空闲内存 694 360 → 693 468 kB（30 min 只少 892 kB，是内核页缓存波动）

结论：**没有内存泄漏**。注意别把 t=0→t=30 的 +2.4 MB 说成"增长"——那是 blob 载入。

## 5. 削波（本次唯一异常项）

30 min 里 21 473 个样本在输出端越界（|v|>1.0，`encode_block` 统计），即 0.019%，
约 12 个样本/秒、每块 ~3.6 个。

- **不是板端问题**：x86 同配置（`--ct-stride 2 --sm-stride 2 --mlp-int8 --stream 300`）
  4 s 也是 86 个越界（板端 smoke 同配置也是 86）。
- **不是交叉淡化造成的**：`--fade-ms 0` 反而更多（101 vs 86），所以是块级 SoundTouch
  重启带来的瞬态峰值（每块重新 flush WSOLA，块头块尾相位不连续）。
- 4 s 批处理（`--dump` 那条路径）是 **0 削波**，与 `README.md` 的"削波 0"一致；
  差异只在流式路径。**建议**：live 档把 `out_gain_q16` 从 39322 降到 ~34000（−1.3 dB）
  再测一轮，或按块做限幅；本次没有改参数（任务只要求测量）。

## 6. 与原有结论的关系

| 旧结论 | 本次 | 关系 |
|---|---|---|
| proc 285 ms/块、延迟 585 ms（12 s ×3） | 纯处理 p50 268.7 ms、e2e p50 568.7 ms | 旧值含 aplay 写阻塞，本次纯处理更低；量级一致 |
| 300 ms 块 0 欠载（12 s ×3） | 30 min 0 欠载 | **从 12 s 扩到 30 min，结论成立** |
| 削波 0（批处理） | 批处理 0、流式 0.019% | 补上了"流式并非 0"这个事实 |
| p50/p95/p99 未测 | 已测 | 缺口关闭 |
| 30 min 长稳未测 | 已测 | 缺口关闭 |

## 7. 产物

```
metrics/logs/stability_20261026/blocks.jsonl           30 min 逐块 JSON（6001 行：6000 块 + summary）
metrics/logs/stability_20261026/aplay.log              aplay 输出（78 B，无 underrun）
metrics/logs/stability_20261026/mem.csv                RSS/空闲内存，30 s × 60
metrics/logs/stability_20261026/env.txt                硬件/时钟/版本/在线 sha
metrics/logs/stability_20261026/analysis.json          本报告全部数字的机器可读版
metrics/logs/stability_20261026/lat_300_fix.csv        60 s 延迟分布（修正版脚本）
metrics/logs/stability_20261026/lat_300_blocks_fixed.jsonl  逐块原始（修正后）
metrics/logs/stability_20261026/lat_300_blocks_raw.jsonl    逐块原始（修正前，用来复现累计值 bug）
metrics/scripts/measure_latency.sh                     修正版
metrics/scripts/measure_latency.sh.orig                原始版（未改，留档）
metrics/scripts/CHANGES_measure_latency_20261026.md    bug 说明
```

## 8. 限制

1. 30 min 是**同一段 4 s 音频循环 450 次**，不是真人连续说话；内容多样性不影响
   CPU/内存结论，但"长稳"不含内容分布变化。
2. 没接音箱做主观听感；"掉音"只能用 underrun 计数 + block 连续性证明，不能证明
   喇叭实际出声（现场若有条件应补一次）。
3. 温度/频率未采集（`scaling_cur_freq` 全程 666 667 kHz；没有 thermal zone 读数），
   报告里不声称"温升已测"。
4. 削波 0.019% 未做主观可闻性判断，只报告数字与复现方法。
