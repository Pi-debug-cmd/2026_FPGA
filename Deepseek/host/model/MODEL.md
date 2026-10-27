# 模型权重说明（`student_v5.blob`）

## 1. 文件

| 项 | 值 |
|---|---|
| 文件 | `student_v5.blob` |
| 大小 | **4,843,308 B** |
| SHA-256 | `c04107b95de35fb3f08125274099c5831e18eeb33e08aa178fb12e00a1ebae4d` |
| 同目录 | `student_v5.json`（元数据，与 blob 一一对应） |
| 来源 | 由训练产物 `models/student_v5.pt` 经 `host/app/export_weights.py` 导出 |
| 许可 | 团队自训练模型；训练语料为团队自有 + 教师伪标签，**不含第三方版权音频** |

## 2. 结构

| 字段 | 值 |
|---|---|
| in_dim | 646（32 ceps + logf0 + voiced + gain + apmean + Δceps32 = 68；±4 帧上下文 → 612；句级统计 34） |
| hidden | 512 |
| layers | 4（GELU，**精确 erf** 形式，不是 tanh 近似） |
| out_dim | 48（倒谱残差阶数） |
| context | ±4 帧 |
| nceps_in / nceps_out | 32 / 48 |
| n_bins | 513（fft_size 1024） |
| frame_period | 10 ms |
| sample_rate | 16000 |
| pitch_ratio | 1.4 |
| 参数量 | **1,143,856** |

附带导出：`mu/sd[646]`（标准化）、`dct_in[32][513]`、`dct_out[48][513]`、
`synth[48][513]`（= `pinv(dct_out).T`）。

## 3. 为什么 `synth` 要单独存

`dct_out` 的行是正交的（`dct_out @ dct_out.T == I`，实测最大误差 1.19e-6），
所以 `pinv(dct_out).T` 与 `dct_out` 只差 **1.86e-9**。理论上可以直接用转置，
但仍然按 `np.linalg.pinv` 原样导出，避免"用近似代替逆变换"的争议。
板上不做 `pinv`（开销大且没必要）。

## 4. 量化版本

- **int8 权重不单独存文件**：运行时由 fp32 权重按 per-channel 方式量化，
  存在 `mlp_int8.inc` 里（同一份 blob，`--mlp-int8` 开关切换）。
- 量化后权重体积 4.57 MB → **1.14 MB**，四项指标变化：
  identity +0.0029、UTMOS −0.0080、CER 0.0000、泄漏 +0.0040。
- int8 与 fp32 的波形 **SNR 41.7 dB、corr 0.99997**（同一输入）。

## 5. 精度与数值契约

| 项 | 契约 |
|---|---|
| 内部精度 | 全链 **double**，仅 MLP 用 float32（与训练一致） |
| 定点点 | 无（MLP 为 fp32/int8，无定点推理） |
| 与 Python 参考 | 逐阶段 max\|Δ\|：f0/logsp/ap = 0；特征 1.5e-5；MLP 残差 9.2e-5；最终波形 121.71 dB |
| 跨架构 | 板端 ARM vs 主机 x86：`x16`/`xb16` 逐字节相同，`y16` 139.38 dB |

## 6. 复现导出

```powershell
$py = "<workspace>/env/venv/Scripts/python.exe"   # 含 torch
& $py host\app\export_weights.py        # 需要 models/student_v5.pt
# 产物: data/student_v5.blob + student_v5.json
```

导出后请核对：
1. `student_v5.json` 的 `sha256` 与 `Get-FileHash student_v5.blob` 一致；
2. 用 `vc_stream_host.exe --model student_v5.blob ... ` 跑一次，遥测里
   `model_bytes=4843308`；
3. 与 `metrics/logs/board_c/board_final_telemetry.json` 对照 `mlp_ms` 量级是否一致
   （不同机器绝对值不同，但不应差一个数量级）。

## 7. 许可与合规

- 训练语料：团队自有录音 + 教师模型伪标签；**未使用任何第三方版权歌曲/影视音频**。
- 教师模型（Seed-VC / RVC）仅用于生成训练目标，**不随本包分发**。
- 本 blob 只包含数值权重，不含任何个人信息；`student_v5.pt` 训练脚本与语料不在本包内，
  如需完整重训请向团队索取。
