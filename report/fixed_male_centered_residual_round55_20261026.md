# PS-20261021-10：零均值源谱动态残差 Round 55

本轮判定 **REJECTED_CENTERED_SOURCE_RESIDUAL**。冻结 Round51 的 gain1.6，只在固定男性 validation 录音4上把源 WORLD 谱 DCT `8:60` 去除逐维时间均值后的动态残差注入候选：

| alpha | 身份 | P10 | 泄漏 | UTMOS | CER |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.0 | .6946 | .6766 | .1046 | 2.2746 | .2500 |
| 0.1 | .6976 | .6813 | .1101 | **2.3042** | .2500 |
| 0.2 | .7001 | .6858 | .1131 | **2.3390** | .3235 |
| 0.3 | .7037 | .6916 | .1197 | **2.3722** | .3088 |
| 0.4 | .7059 | .6946 | .1214 | **2.3991** | .2941 |

残差随比例增加能单调提高身份与UTMOS，但也单调增加严格源泄漏；CER没有改善到 `<=0.15`。既定最小门比例仍选择 alpha0.0，没有候选五门全过，因此拒绝该机制并保持录音5锁定。

复现入口为 `build/apply_world_temporal_postfilter_round47_20261026.py --source-residual-alphas 0 0.1 0.2 0.3 0.4 --source-residual-cutoff 8`，原始逐窗严格指标保留在忽略目录 `build/generated/hubert_world_round55_20261026/strict_metrics.json`。

本轮未播放、未录音、未接触板卡；无真人听感、Cortex-A9、实时、Vivado、RTL或PL结论。
