# PS-20261021-10：显式源韵律输入预检 Round 32

## 结论

本轮 **READY_PROSODY_TRAIN**。Round 25 的 200 对源音频全部通过 manifest 与缓存清单双重 SHA-256 校验，提取的源 log-F0、VUV、log-energy 全部有限。源韵律对教师目标提供显著、非退化的信息，可以进入单变量训练。

- 句内中心化 log-F0 轮廓相关：`0.5582`。
- log-F0 一阶动态相关：`0.1558`。
- 句内归一化能量相关：`0.9409`。
- VUV 准确率 / F1：`0.8685 / 0.9210`。
- 共同有声帧：`35,720`。

这说明源能量和清浊边界几乎可直接传递，源 F0 轮廓也包含明显韵律信息；F0 短时增量相关较弱，不能简单复制源 F0，仍需学习到目标女性范围的映射。

## 预算

把冻结 PCA 后的 HuBERT 输入从 96 维扩为 `96+3=99` 维，只增加首层 `3×192=576` 个参数：总参数 `477,771→478,347`，增加 `0.1206%`。每帧增加 576 MAC，按 50 Hz 为 28,800 MAC/s；相对当前估算每帧 475,200 MAC 增加 `0.1212%`。

离线预检使用 WORLD Harvest、StoneMask、CheapTrick，不是因果或板端实测。部署设想仅允许复用现有源 F0/能量分析链；其因果特征与离线特征的一致性必须在后续单独验证。

## 复现与边界

```powershell
$env:FPGA_ASSET_ROOT='C:\Users\World\Desktop\2026_FPGA'
$env:KMP_DUPLICATE_LIB_OK='TRUE'
& 'build\generated\python312\cpython-3.12.13-windows-x86_64-none\python.exe' build\audit_source_prosody_round32_20261025.py --asset-root 'C:\Users\World\Desktop\2026_FPGA'
```

本轮没有训练、使用 Track 9、固定男性输入或播放。板卡保持关机。
