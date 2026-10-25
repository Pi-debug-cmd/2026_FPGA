# PS-20261021-10：扩展教师配对 HuBERT→WORLD Round 25 预检

## 结论

本轮状态为 **READY_LONG_TRAIN**。现有配对资产完整、说话人切分无泄漏，HuBERT/WORLD 缓存 200/200 成功，可以进入独立的长训练轮次。

- 训练：192 对、20 名说话人、`888.1089 s`。
- 验证：8 对、2 名说话人、`46.1948 s`。
- 总量：`934.3038 s`，约 15.57 分钟。
- 训练/验证说话人交集：空。
- Track 9：未使用。
- 固定男性录音：未使用。
- 缓存：200 个 NPZ，共 `79,280,418` 字节；每帧 768 维冻结 HuBERT 内容和 75 维 SP60/AP12 WORLD 教师目标。
- 缓存清单 SHA-256：`57dc9d95bb4b485ca5325b4e318766ef852bdfd29d49e5c197c804de8980d053`。

首、中、末三个缓存抽检均为内容 `(T,768)`、目标 `(T,75)`，且全部有限。源/教师原始 `.f32` 在缓存前逐件核对 manifest SHA-256；任何不一致会立即失败。

## 风险与边界

教师来自既有 CosyVoice3 source-timed VC，未获真人听感接受，不能把教师或训练损失直接当成保底方案通过。长训练必须继续使用独立验证说话人早停，冻结后才运行固定男性录音 4/5；通过五门后才能请求真人试听。

缓存、教师波形和模型资产保留在忽略目录，不进入 Git。板卡保持关机，本轮未录音、播放或访问板卡。

## 复现

```powershell
$env:FPGA_ASSET_ROOT='C:\Users\World\Desktop\2026_FPGA'
& 'C:\Users\World\AppData\Local\Python\pythoncore-3.12-64\python.exe' build\prepare_hubert_world_pairs_round25_20261025.py --asset-root 'C:\Users\World\Desktop\2026_FPGA'
```

