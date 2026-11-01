# Skill 包：可迁移的 PYNQ / Zynq 工程技能

> 这三条 skill 不是"本项目的说明书"，而是**这套硬件开发里反复咬人的三个点**的成品化封装：
> overlay 怎么确认真的加载了、DMA 数据为什么偶尔被清零、以及"跟参考实现差多少"怎么变成判定。
> 每一个都写清了**换题目/换板卡还能怎么用**（见各自的 README 第 6 节）。

## 目录

| skill | 一句话 | 关键产物 | 已验证 |
|---|---|---|---|
| [`overlay_load_and_verify/`](overlay_load_and_verify/README.md) | 通用 Overlay 加载 + 回滚 + 寄存器回读校验 | `overlay.py`（状态机 + journal + 回滚）、`regtool.py`/`regtool.c`（寄存器表驱动验收） | fpga_manager `operating→operating`、GPIO 5/5 组读写一致、回滚镜像 SHA 与历史一致 |
| [`dma_cache_coherency/`](dma_cache_coherency/README.md) | DMA 与 cache 一致性封装 + **常见出错情形定位清单** | `dmabuf.{h,c}`（非缓存别名 / cached+sync 两种策略）、`dma_roundtrip.c`（30 秒自检）、`diag_checklist.md` | 首轮 16 样本错（2×8 全 0）→ 修复后 128000 样本 `max_abs_diff=0` |
| [`golden_reference_compare/`](golden_reference_compare/README.md) | 黄金参考自动比对 + 性能/资源自动采集出报告 | `golden_compare.py`（两级门禁 + 失败形状分类）、`collect_metrics.py`（Vivado+遥测→CSV） | 4 组真实比对与文档数字一致；4 种注入故障分类全对 |

## 它们怎么串起来（本项目就是这么用的）

```
上电
 └─ overlay_load_and_verify:  记录状态 → 解绑旧消费者 → 加载位流 → 回绑 → 寄存器回读
      └─ dma_cache_coherency: 分配一致性缓冲 → DMA 往返 → 断言 bit-exact
           └─ golden_reference_compare: 与 Python/RTL 参考比 → 出判定 + 指标表
                └─ collect_metrics: 资源/时序/RTF 汇总成可追溯的 CSV
```

每一步的**失败都会立刻被下一步挡住**，而不是等到听感或演示时才暴露：
寄存器没生效 → `regtool` 非零退出；缓存不一致 → `dma_roundtrip` 报 32 B 零段；
算法不对 → `golden_compare` 给出形状分类。

## 为什么这三条"通用性高"

1. **不含本题的业务名词**：三条 skill 的代码里没有 "pitch"、"WORLD"、"voice" 之类的词；
   基地址、寄存器表、消费者清单、比对数据全部由外部参数/JSON 传入。
2. **失败模式是平台级的，不是题目级的**：Zynq-7000 的 HP 口非一致、
   `cacheflush` 只清 L1、`fpga_manager` 需要 4 字节反转镜像——换成图像/CNN/雷达项目一模一样。
3. **判据是硬指标**：`max|Δ|=0`、`SNR≥100 dB`、`fpga_manager=operating`、
   寄存器读回一致，不依赖主观判断。
4. **换板卡只改常数**：基地址、L2 大小、页数上限、消费者清单都是参数。

## 复用记录（本仓库内真实发生过的）

- `overlay.py` 在**两个完全不同的 PL 设计**上没改一行（视频/GPIO 底板 → 音频变调核），
  只换了 `consumers.txt` 与 `--rebind`。
- `dmabuf.c` 的教训直接复用到同一板的另一条 DMA 路径（M3 与 stage-2 音频流），
  避免了第二次踩同一个坑。
- `golden_compare.py` 在本项目之外还被用来核过 `pitch_dma_mem` 重编译产物的
  SHA 一致性（源码 → 二进制的可复现性）。

## 环境依赖

- `overlay.py` / `golden_compare.py` / `collect_metrics.py`：Python 3.8+；
  `golden_compare` 需要 numpy；其余仅标准库。
- `regtool.c` / `dma_roundtrip.c` / `dmabuf.c`：任意 `arm-linux-gnueabihf-gcc`（已用
  Vivado SDK 2018.3 的 GCC 7.3.1 交叉编译验证，`-Wall -Wextra` 零警告）。
- 板端需要 root（`/dev/mem`、`/sys/class/fpga_manager`、`/proc/self/pagemap`）。
