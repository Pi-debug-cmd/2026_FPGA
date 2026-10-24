# PS-20261021-10：固定男性 WORLD 延伸优化（2026-10-24）

## 结论

本轮 **REJECTED**，不部署到板卡，也不请求试听。

保留 `world_budget_v23` 实时框架，先尝试固定男性源专用 WORLD 音高/谱形/AP 映射，再把历史 A3 高身份包络作为受控支路与 WORLD 在参数域融合。第二轮锁定句把目标身份从历史 A1 的 0.1903 提高到 **0.5650**，CER 从 0.1667 改善到 **0.1000**；但源泄漏 **0.1968 > 0.10**、UTMOS **1.9631 < 2.30**，没有同时通过四项客观门。按频带保留 WORLD 高频细节也没有形成合格交点。

本轮只做电脑端离线运算，没有录音、播放、板卡、Vivado、RTL、PL、实时或真人听感测试。当前板上运行版本未改变。

## 防泄漏协议

- 固定男性录音 1～3：只建立源画像。
- 固定男性录音 4：只用于候选选择。
- 固定男性录音 5：候选冻结后才首次加载并评价。
- 女声 Track 5～8：目标画像与目标声纹质心。
- 女声 Track 9：不参与候选选择；只作独立目标说话人核查。

输入文件 SHA-256 见机器可读报告 `report/world_fixed_male_optimization_20261024.json`，与 `report/fallback_one_to_one_assets_20261021.json` 的源侧清单一致。

## 结果

| 轮次 | 冻结候选 | 身份 ↑ | 泄漏 ↓ | UTMOS ↑ | CER ↓ | 判定 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 历史 A1/WORLD 参考 | 原闭环 | 0.1903 | 0.1719 | 2.0354 | 0.1667 | 四项均未过现行门 |
| 源专用 WORLD 网格 | warp 1.20、detail 0.75、9 dB clamp | 0.3557 | 0.2449 | 1.6258 | **0.1250** | 仅 CER 通过 |
| WORLD+A3 参数融合 | WORLD 0.40 + A3 0.60 | **0.5650** | 0.1968 | 1.9631 | **0.1000** | 身份/CER 通过，泄漏/UTMOS 失败 |

现行门槛为身份 ≥0.45、P10 ≥0.35、泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15。单一锁定句不能计算有意义的跨句 P10，因此即使其余四项通过，也仍需多句锁定验收和冻结后的新会话句。

验证集的权衡关系很清楚：

- A3 权重 0.60：身份 0.513、泄漏 0.141、UTMOS 1.899、CER 0.147；最接近内容门，但泄漏/自然度仍失败。
- A3 权重 0.80：身份 0.583、泄漏 0.091 已通过身份/泄漏，但 UTMOS 1.564、CER 0.382，内容和自然度严重退步。
- A3 权重 1.00：身份 0.570、泄漏 0.046，UTMOS 1.587、CER 0.353；再次复现“身份提高但模糊”的历史 A3 失败模式。
- 频带融合最佳候选仍未同时满足泄漏、自然度和内容；保留 WORLD 高频不能修复 A3 的核心包络预测误差。

因此不存在可以通过调一个混合比例得到的合格点。本轮不继续扩大同类参数搜索。

## 实现与复现

- `src/reference/world_fixed_male_mapping.py`：可测试的源专用 F0、谱形、AP 数值映射。
- `build/optimize_world_fixed_male_20261024.py`：纯 WORLD 网格、验证选择和冻结后锁定评价。
- `build/blend_world_a3_fixed_male_20261024.py`：WORLD+A3 全频/分频参数融合。
- `sim/test_world_fixed_male_mapping.py`：映射边界、能量保持、音高和 AP 测试。

运行命令（`--asset-root` 指向含现有忽略依赖的本机项目根目录）：

```powershell
python -m unittest sim.test_world_fixed_male_mapping -v
& 'C:/Users/World/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -u build/optimize_world_fixed_male_20261024.py --asset-root 'C:/Users/World/Desktop/2026_FPGA'
& 'C:/Users/World/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -u build/blend_world_a3_fixed_male_20261024.py --asset-root 'C:/Users/World/Desktop/2026_FPGA'
python -m json.tool report/world_fixed_male_optimization_20261024.json
```

候选 WAV 和完整逐候选结果只在 `build/generated/`，不进入 Git。A3 checkpoint `a3_content.pt` 为本机忽略资产，491321 字节，SHA-256 `46ebff5951216b8b63ab7fd7a509c2dc10ddec7dbcbdb93e65fa8490d5d96b13`；LLVC `reduced_student_v2/final.pt` 也是本机忽略资产，6607655 字节，SHA-256 `5a3f5de6f7bef12a29323be5bb88168025d85080b527933e8f3f54cbf07a9641`。因此本轮代码可审查，但失败候选不构成跨电脑模型交付。

## 下一步

继续使用 v23 作为清楚、连续的板端运行保底；音色提升应转向能保留内容与自然度的更强语义教师/声码器方案，而不是继续增加 WORLD 静态谱形或 A3 混合强度。新路线仍须先在同一 1～3/4/5 协议下通过全部客观门，再申请本地试听。
