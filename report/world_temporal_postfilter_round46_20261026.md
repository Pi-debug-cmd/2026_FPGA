# PS-20261021-10：非 F0 时间对比度后滤波 Round 46

## 结论

本轮判定 **GO_GAIN_1_4**。冻结 Round37 checkpoint，仅将预测谱、能量和非周期性三组相对每句时间均值的偏差乘同一增益；log-F0、VUV、模型和合成器均不变。

| 增益 | 8句 UTMOS | SSB0080 | SSB0434 |
| ---: | ---: | ---: | ---: |
| 1.0 | 2.0055 | 2.1205 | 1.8904 |
| 1.1 | 2.1491 | 2.2802 | 2.0180 |
| 1.2 | 2.2499 | 2.3937 | 2.1060 |
| 1.3 | 2.3331 | 2.4714 | 2.1947 |
| 1.4 | **2.4082** | **2.5371** | **2.2793** |

相对1.0基线，1.4使总体和两个说话人分别提高 `+0.4028/+0.4166/+0.3889`，通过“总体改善且两个说话人均不退步”的预设选择门。1.4位于预设网格边界，但本轮不扩展网格，避免继续在验证集追涨；Round47冻结1.4并只在 Track 9 运行一次身份/P10/UTMOS/CER回归。

该后处理不增加模型参数，只增加逐维均值与缩放。当前仍是目标教师验证，不表示固定男性转换已经通过。

## 复现

使用 cp312 项目运行时，并把项目已有 `world_deps`、`llvc_cpu_deps`、`seed_audio_deps`、`seed_cpu_deps`、`eval_deps_20261016` 加入本轮进程 `PYTHONPATH`：

```powershell
python build/sweep_world_temporal_postfilter_round46_20261026.py --asset-root <repo-with-assets> --generated-root <round25-cache-root> --checkpoint <round37-checkpoint> --output <generated-output>
```

## 边界

只使用8条 validation 句选参；未使用 Track 9、固定男性锁定句、播放、录音或板卡。生成 WAV 留在 `build/generated/`，未提交 Git。
