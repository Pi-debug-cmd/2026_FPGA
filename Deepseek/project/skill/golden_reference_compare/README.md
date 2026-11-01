# golden_reference_compare — 黄金参考自动比对 + 性能资源自动采集

> 一句话：把"和参考实现比一下"变成**可判定的两级验收**，并且把"错的形状"直接翻译成
> 故障类别（缓存回写 / 定点舍入 / 查表漏插值 / 群延迟 / 系统性缩放）；
> 再把 Vivado 报告与程序遥测自动抽成一张可追溯的 CSV。

## 1. 为什么不是"diff 一下就完事"

同一条 diff，形状不同，根因完全不同。我们实际遇到过的四种：

| 形状 | 真实根因 |
|---|---|
| 两段各 8 个样本、全 0、32 B 对齐 | L2 脏行回写（`skill/dma_cache_coherency`） |
| 每个 bin、每一帧都错，误差同号 | 查表漏 frac 插值 / 索引错位（49248/49248 bin 全失配） |
| 波形差 1–2 LSB、无结构 | 定点舍入方向不同（round-half-up vs 算术右移） |
| 最佳时延 ≠ 0 | 重采样器群延迟（127 抽头 → 31.5 个样本，必须改成整数） |
| 处处都差、但差 ≤ 1e-3 × RMS | 1 ulp 输入差被 4×512 GELU 放大 10³ 倍（**不是实现差异**） |

所以工具必须输出：`max_abs_diff / SNR / corr / runs / zero_runs / first_bad /
frames_bad / bins_bad / lag`，而不只是一个布尔值。

## 2. 目录

```
golden_reference_compare/
├── golden_compare.py     # 比对器：格式自识别 + 整数时延对齐 + 形状分类 + 两级门禁
├── collect_metrics.py    # Vivado 利用率/时序 + 程序遥测 → long-format CSV/MD
├── report_template.md    # 结果表的固定格式（每个数字都带来源）
└── example/
    ├── gen_demo.py       # 回归测试：注入 4 种已知故障，检查分类是否正确
    ├── results_table.md  # 真实数据上的比对结果（本文件由工具生成）
    ├── out_x16.json / out_y16.json
    └── demo/             # gen_demo.py 的临时产物（可删）
```

## 3. 快速开始

```bash
# 1) 比对两块 float32 dump（板端 vs 主机），默认 100 dB 门限
python3 golden_compare.py board/x16.f32 host/x16.f32 --label arm_vs_x86

# 2) 401 帧 × 513 bin 的包络：按帧/按 bin 定位
python3 golden_compare.py ref/logsp.f32 dut/logsp.f32 --shape 401x513

# 3) 16-bit PCM 裸流（DMA 往返），容差 2 LSB
python3 golden_compare.py in.raw out.raw --dtype i16 --tol 2

# 4) 把资源/时序/RTF 收成一张表
python3 collect_metrics.py --vivado-dir ../../fpga/report \
    --telemetry ../../metrics/logs/board_c/*.json \
    --out ../../metrics/resource_timing.csv --md ../../metrics/resource_timing.md \
    --meta board=xc7z020clg400-2 --meta clock_mhz=100

# 5) 回归自检（不需要板卡）
python3 example/gen_demo.py
```

退出码：`0` 通过 / `1` 不通过 / `2` 用法或 IO 错。可直接塞进 CI。

## 4. 设计要点

1. **两级门禁**：`bit_exact`（max|Δ|=0，RTL vs 定点模型用）与 `numeric`
   （max|Δ|≤tol 或 SNR≥snr_min，浮点流水线用）。只有一层门禁时，
   "差 1 LSB"和"整段错"会被混为一谈。
2. **先对齐、再判断**：默认在 ±512 样本内搜最大相关时延；`lag≠0` 本身就是一个发现
   （我们的 127 抽头重采样器必须把群延迟凑成整数 31 个样本，否则对齐比较永远差半样本）。
3. **形状分类是硬编码的领域知识**：分类规则写在 `verdict_text()` 里，
   每条都对应一个真实故障；`example/gen_demo.py` 是它的回归测试。
4. **度量必须带来源**：`collect_metrics.py` 输出 `source` 列（哪个报告文件），
   评审可以自己 re-derive，而不是相信截图。
5. **不猜格式**：后缀决定 dtype（`.f32`/`.raw`/`.npy`/`.wav`/`.csv`），
   也可以 `--dtype` 覆盖；长度不一致会 WARN 而不是静默截断。

## 5. 失效条件

- **不是同一内容的两个信号**（例如 WSOLA vs 相位声码器两种变调算法）：
  样本级 SNR 没有意义（我们实测 −9.3 dB / corr 0.21），此时应改用**包络域**分带比较。
- **允许的时延随块变化**（流式块拼接）：全局 lag 搜索会掩盖"每块边界错一点"，
  要按块分段比对。
- **非平稳信号的幅度门限**：`--tol` 是绝对 LSB，浮点信号请用 `--snr-min` 而不是调 tol。
- **`--shape` 与样本数不整除**：会 WARN 并退回 1-D，此时按帧/按 bin 的定位不可用。
- **需要统计显著性**（不是逐样本）：这工具不做置信区间，只做逐样本/逐帧判定。

## 6. 换题目 / 换板卡还能怎么用

- **换算法**（图像、雷达、CNN 推理）：只要 DUT 能 dump 成数组，比对与门禁逻辑不变；
  2-D 定位会自动切成"哪几帧/哪几个 bin"。
- **换平台**（Zynq → PC / GPU / MCU）：同一份 golden 数据、同一套门限，
  跨平台一致性可以直接出表（本项目就是 ARM vs x86 = 139 dB 这样来的）。
- **换到 PYNQ**：`pynq` 侧 dump 成 `.npy` 直接喂进来，不需要改一行。
- **做 CI 门禁**：`gen_demo.py` 那种"注入已知故障 → 断言分类"的写法可以搬到任何
  RTL/HLS 工程的回归套件里。
- **资源/时序采集**：`collect_metrics.py` 的正则只依赖 Vivado 报告的表格格式，
  换器件、换版本（2018.3 / 2022.2 / 2026.1）都不用改。

## 7. 已验证结果

`example/results_table.md` 是在**真实数据**上跑出来的（不是构造数据）：

| dut | 结果 |
|---|---|
| 板端 ARM vs 主机 x86 的 `x16` | `max_abs_diff = 0`，bit-exact |
| 板端 `y16` vs Python oracle（喂 1 ulp 不同的输入） | 74.86 dB → 判为"numeric axis"，与人工定位一致 |
| `logsp` 401×513 两个配置 | bit-exact |
| fp32 vs int8 权重 | 41.67 dB（与报告写的 41.7 dB 一致） |

`example/gen_demo.py` 的四种注入故障全部分类正确（DEMO PASS）。
