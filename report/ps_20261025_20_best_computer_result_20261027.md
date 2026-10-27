# PS-20261025-20 电脑端最佳结果汇总

日期：2026-10-27；角色：Remote-PS-C。来源为 Fixed-Male4 strict evaluation，使用既定五项门槛。

## 综合最接近门槛：v21

按 strict evaluator 的 `minimum_gate_ratio` 排序，v21 最高，为 0.423624683。指标：identity 0.758199834，identity P10 0.733886861，leakage 0.236058011，UTMOS 2.522906144，CER 0.352941176。身份、P10、UTMOS 通过；leakage 和 CER 未通过。

## CER 最接近门槛：v18

v18 CER 为 0.161764706，是可用实验版本中最接近 CER≤0.15 的结果；其 identity 0.763452809，P10 0.747618627，leakage 0.238312337，UTMOS 2.421749751。CER 与 leakage 仍未通过，因此不是可发布模型。

## 其他边界结果

- v16 的 leakage 最低于保持身份、UTMOS通过的训练版本：0.232333038；但 CER 为 0.411764706。
- v25 的 leakage 最低：0.159276669；但 identity 0.143637836、UTMOS 1.299219171、CER 1.0，整体崩溃，不作为最佳可用结果。
- v1–v25 没有版本通过全部五项门槛。不得进入 `WAIT_LOCAL_TEST`，不发布模型包。

边界：只做电脑端离线运行；Male5 与 Track9 未读取；没有播放、录音、试听、板卡、ARM、Vivado、RTL、PL 或实时验证。
