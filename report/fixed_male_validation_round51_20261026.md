# PS-20261021-10：固定男性 validation 转换 Round 51

## 结论

本轮判定 **REJECTED_CONTENT**。冻结 Round37 checkpoint 与 gain1.6，首次转换固定男性 validation `标准录音 4.wav`：

`身份 0.6946 / P10 0.6766 / 泄漏 0.1046 / UTMOS 2.2746 / CER 0.2500`

身份和P10明显通过，证明输出已经强烈靠近目标女声；泄漏只高 `0.0046`、UTMOS只低 `0.0254`，但 CER 高于0.15，当前不能进入锁定录音5或试听。

录音4是允许选参的 validation。Round52 可在同一录音上扫描已验证后滤波的 gain，但必须冻结 checkpoint、参数组和评估器；选择时以五门最小比例优先，不能只追身份或UTMOS。录音5继续保持锁定。

## 边界

未使用 Track 9 或锁定录音5，未播放、未录音、未接触板卡。
