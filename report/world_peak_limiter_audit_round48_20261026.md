# PS-20261021-10：峰值限制可归因性 Round 48

## 结论

本轮判定 **NO_GO_LIMITER_TUNING**。`synthesize()` 在峰值超过 `0.98` 时只执行全局线性缩放 `signal *= 0.98 / peak`，没有逐样本硬削波、压缩曲线或时变增益，因此不改变相对波形。

严格评估器在输入 UTMOS 前又执行 RMS 归一化：`normalized = clip * 0.04 / rms(clip)`。对于任意正比例 `k`，有：

`(k*x) * 0.04 / rms(k*x) = x * 0.04 / rms(x)`

因此 Round47 的 `peak_before_limit=2.0804` 不能通过更换全局峰值缩放提高 UTMOS；继续调限制器只会制造无效轮次。Round49 回到原8条 validation，预先声明扩展 gain `1.5/1.6/1.7/1.8`，仍要求两个验证说话人都不退步，再冻结一个候选。

## 边界

本轮只读 `synthesize()` 与严格评估器代码和 Round47 既有数值，没有训练、合成新音频或重新使用 Track 9；未用固定男性输入、未播放、未接触板卡。
