# measure_latency.sh 修正记录（2026-10-26）

## 症状

原脚本在板上跑 `sh measure_latency.sh 300 60 in.raw lat_300.csv`，输出：

```
block_ms,blocks,proc_min_ms,proc_p50_ms,proc_p95_ms,proc_p99_ms,proc_max_ms,proc_mean_ms,...
300,200,237.8,26095.90,49350.20,51515.50,51793.4,26107.11,...
```

`proc_p50_ms = 26 095.9 ms`、`proc_max_ms = 51 793.4 ms`——单块不可能用 26 秒，
51 793.4 恰好等于整跑 60 s 的**累计**处理时间（`rtf 0.8632 × 60 s`）。

## 根因

`vc_live` 的逐块 JSON 打印的是**累计**计数，不是本块耗时：

```cpp
// src/stream_mode.inc:215
st.proc_ms += now_ms() - tb;          // 累加
...
"\"block_rtf\":%.3f,...", st.proc_ms, st.proc_ms / audio_ms,   // 打印的是累计值
```

所以 `proc_ms` 在 block 1..200 上单调递增（237.8 → 474.8 → 715.3 → …），
`block_rtf` 同理（`cum_rtf` 才是真实的平均 rtf）。
原脚本的

```sh
awk '{ if (match($0, /"proc_ms":[0-9.]+/)) { s = substr($0, RSTART+10, RLENGTH-10); print s } }'
```

把累计值当成分位数样本，于是 p50 变成"跑到一半时的累计耗时"。

## 修正

1. 只取 `{"block":...}` 开头的行（排除末尾的 summary 行，那里的 `proc_ms` 是总和），
   对累计值取**一阶差分**，得到每块处理时间。
2. 增加一致性自检：差分之和应等于 summary 里的累计总和（本次 51 867.20 vs 51 867.18，
   差 0.02 ms，只是 0.1 ms 量化误差）。
3. `BYTES_PER_SEC` 从 1024000（= 4 s 的字节数，单位标错）改为 256000，`REP` 不再多喂 4 倍数据。
4. 其它输出列与用法不变。

原文件保留为 `measure_latency.sh.orig`，未改动；修正版即 `measure_latency.sh`。

## 修正后（2026-10-26，COM8，vc_live sha 83257578…）

```
block_ms,blocks,proc_min_ms,proc_p50_ms,proc_p95_ms,proc_p99_ms,proc_max_ms,proc_mean_ms,e2e_p50_ms,e2e_p95_ms,e2e_p99_ms
300,200,233.000,268.70,276.70,277.90,278.10,259.34,568.70,576.70,577.90
```

原始逐块日志：`logs/lat_300_blocks_fixed.jsonl`（修正版脚本产出）、
`logs/lat_300_blocks_raw.jsonl`（修正前那一轮，用来复现这个 bug）。

> 说明：这一轮 `stdout` 接 `/dev/null`，量的是**纯处理**分布（脚本头部就是这么定义的）。
> 接 aplay 的端到端/欠载是另一件事，见 30 min 长稳那份记录。
