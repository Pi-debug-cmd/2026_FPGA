# evidence — 图像证据

只有两张图，都是**同一段 4 s 素材**在三条链路上的对照。资源/时序不提供截图，
因为 `../fpga/report/` 里的原始文本报告更可核（截图无法 grep）。

## 1. `stage2_compare.png`

三联对照（波形 + 语谱图），从上到下：

| 行 | 内容 |
|---|---|
| A | 电脑端参考（librosa 相位声码器 + v5 包络）——电平低约 9.5 dB，语谱图有明显相位声码器的"涂抹" |
| C | 板端 stage-1（精确两遍 WORLD + fp32 MLP） |
| E | 板端 stage-2 最终（D4C 隔帧 + 第二遍 WORLD 并行 + 单精度 FFT） |

读法：**C 与 E 几乎无法区分**（E−C 波形相关 0.99975、UTMOS 差 0.0018），
说明所有性能优化没有改变听感；A 与 C/E 的差别主要是电平与相位质量。

## 2. `board_run_overview.png`

板端整链的输入/输出波形 + 语谱图（同一 4 s）。用于确认：
- 输出长度正确、非静音、无削波（峰值 0.8166 FS，`clipped_samples=0`）；
- 音高整体上移（语谱图的谐波条带间距变大）；
- 包络形状与输入一致（不是"换了一个人说话"，而是同一句话换了音色）。

## 3. 怎么重新生成

```powershell
# 板端结果校验 + 出图（原仓库脚本）
& $py metrics\scripts\analyze_board.py --board <board_out_dir> --ref-same <ref_dir> --out-wav <dir>
& $py make_figure.py          # 需要原 board_c 的 out/ 布局
```

> 这两个脚本依赖原工程的 `out/` 目录结构（参考链 npz、各阶段 dump），
> 本包只带了成品图与脚本；要**从零重画**，需要先按 `README.md` 第 3 节跑完参考链。

## 4. 建议补拍的证据（未做）

1. 板卡 + 接线 + 播放中的实物照片（赛事通常要求"作品在板上跑通"的可视证据）。
2. Vivado 的 `report_utilization` / `report_timing_summary` 截图（虽有文本，截图更直观）。
3. 30 min 长稳时的 CPU 占用/温度曲线（配合 `metrics/scripts/measure_latency.sh`）。
