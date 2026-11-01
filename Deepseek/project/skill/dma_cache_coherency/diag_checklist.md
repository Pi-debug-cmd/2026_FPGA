# DMA / cache 一致性诊断清单（现象 → 根因 → 定位命令 → 修复）

这份清单不是"缓存知识科普"，而是**我们 2026-10-25 在 Zynq-7020 上真实排过的故障**的复现卡。
每一条都给出可以在板上 30 秒内跑完的定位命令。

前提：Cortex-A9 + PL310 L2 + AXI DMA（S2MM/MM2S）把数据搬进 PL 再搬回 DDR，
PS 侧用 `/dev/mem` 或 `udmabuf` 之类的用户态缓冲区做数据源/目的地。

---

## 0. 先做一件事：把"是不是一致性问题"变成可判定的

```c
/* 一次 identity 往返：CPU 写 pattern → DMA → PL(直通) → DMA → 比较 */
dma_roundtrip --dma 0x40400000 --words 128000 --chunk 4096 --pattern ramp
```

`dma_roundtrip`（本目录）会在 30 秒内给出：`mismatch / runs / zero_runs /
zero_runs_32B_aligned / max_zero_run / first_bad / max_abs_diff`。

**判读表**：

| 输出特征 | 指向 |
|---|---|
| `mismatch=0` | 这条路径在这一刻是一致的（不代表下次分配也对，见 §1） |
| `zero_runs_32B_aligned>0`，`max_zero_run=8`（int16） | **脏 cache line 回写**，§1 |
| 大段连续失配、`first_bad=0` | 地址/位宽/字节序错，或 PL 不是直通模式，§4 |
| `max_abs_diff` 恒为 1–2 LSB、无零段 | 定点舍入口径不同，不是一致性问题 |
| 每块只有开头/结尾几个样本错 | DMA 长度或 TLAST 差一个 beat，§4 |
| 同一进程第一轮错、第二轮对 | **典型 cache 写回**，§1（这是最强指纹） |

---

## 1. 最坑的一条：DMA 输出被"清零"了 32 字节（我们的真实故障）

**现象**
4 s / 128000 样本的比对里，只有 16 个样本不对，而且是**两段、每段正好 8 个样本**，
位置不连续、值全为 0，其它样本 bit-exact。第二次跑同样的程序，结果可能完全正确。

**根因**
用户态缓冲页在 `mmap`+`memset` 之后是**脏的**（L1 和 PL310 L2 里都是 0）。
`dma_buf_alloc` 里随即用 `/dev/mem` 把同一块 DRAM 映射成**非缓存别名**给 CPU 用。
于是同一物理页有两个虚拟地址：一个 cached（`anon`），一个 uncached（alias）。
CPU 之后只写 alias，但 cached 那份的脏 0 行还在 L2 里。
DMA 把结果写进 DRAM 之后，PL310 因为容量压力把那些脏 0 行**回写**，
正好盖掉 DMA 刚写的 32 B —— 表现为"8 个样本变 0"。

**为什么 `cacheflush` 不管用**
ARM 私有 `cacheflush`(0x0f0002) 只 clean/invalidate **L1 D-cache**，
PL310 L2 是**外部**控制器，这条 syscall 不碰它。我们在板上验证过：
只加 `cacheflush`，16 个样本仍然错；改成"`cacheflush` + L2 冲刷"后立刻 `max_abs_diff=0`。

**定位命令**（按顺序，30 秒）

```sh
# 1) 复现：每次重新分配缓冲，必然能在第一轮打出来
./dma_roundtrip --dma 0x40400000 --words 128000 --repeat 10 --realloc --pattern ramp
#    看 zero_runs_32B_aligned 和 max_zero_run(=8)

# 2) 确认不是 RTL：把 PL 设成恒等（ratio=65536），直接比输入输出
#    仍错 -> 是 PS 侧内存一致性，不是逻辑

# 3) 确认脏行来自 L2：在 DMA 前把 L2 冲刷一遍，如果错误消失即坐实
#    （代码路径：dmabuf.c:dma_l2_scrub，2 MiB = 4×L2，再 usleep 20 ms 等回写落地）
```

**修复（三选一，按推荐度）**

1. **只用非缓存别名**（本 skill 的默认）：CPU 永远不碰 cached 映射；
   分配时做一次 `cacheflush` + L2 冲刷，把初始化的脏行赶出去。
   → 实测 `max_abs_diff=0`，128000/128000 样本一致。
2. **用 CMA/udmabuf/reserved-memory + `mmap` 非缓存属性**：从设备树预留一段
   `no-map` 或 `shared-dma-pool`，驱动侧 `dma_alloc_coherent`。
   产品化应该走这条，但要改 DTB，比赛现场不一定有这个时间。
3. **每次 DMA 前显式 clean 整个缓冲区**：`cacheflush(range)` + `dsb`。
   注意：**只 clean L1 不够**，必须确保没有 L2 脏行（冲刷或用非缓存别名），否则问题会以
   "偶发、只在第一次、只错 32 B"的形式回来。

**判据**：`dma_roundtrip --repeat 20 --realloc` 全部 `mismatch=0`。

---

## 2. DMA 读到旧数据（CPU 写了，PL 收到的是上一次的）

**现象**：PL 侧算出来的结果对应的输入滞后一块；或者第一块输入是 0。

**根因**：CPU 的 store 还在 L1/L2 的 write-back 缓存里，DMA 直接读 DRAM。

**定位**

```sh
./dma_roundtrip --pattern prbs --words 4096 --chunk 4096     # 单块，必错
# 在 DMA 前加 dma_sync_for_device()（clean+scrub）后重跑，若变对 -> 坐实
```

**修复**：写完后 `clean` 该范围（L1）**并**确保 L2 无脏行；或直接用非缓存别名。
注意 AXI **HP 口不是 cache-coherent 口**（ACP 才是），所以"我接的是 HP 口，应该一致"是错的。

---

## 3. CPU 读到旧数据（DMA 写了，CPU 读到缓存里的旧值）

**现象**：DMA 完成标志已置位，CPU 读输出仍是 0 或上一轮的内容。

**根因**：CPU 之前读过这块内存，行在 L1/L2 里是 clean 的旧值；DMA 更新了 DRAM，CPU 命中缓存。

**定位**：`dma_roundtrip` 的第二次 `--repeat`（复用同一缓冲、不 realloc）会出现"读到的还是上一轮 pattern"。

**修复**：DMA 完成后 `invalidate` 该范围（`cacheflush` 在该范围上做 clean+invalidate 即可，
因为此时缓存行是 clean 的），或全程用非缓存别名。

---

## 4. 不是一致性问题，但长得像：地址 / 长度 / 位宽

| 现象 | 真正原因 | 定位 |
|---|---|---|
| 全 0 输出，DMA `SR.Idle=1` 且无 error | S2MM 目标地址写错（比如写了虚拟地址） | 打印 `dma_buf_phys()`，和 `/proc/iomem` 对照 |
| 输出错位半个样本 / 全是噪声 | 输入按 int16 打包但 DMA 按 32-bit 搬（或反之） | 用 `--pattern ramp`，看第一个错点的数值差是否是 65536 的倍数 |
| 每块最后 1–2 个样本错 | `LEN` 与实际 beat 数不一致，TLAST 提前/滞后 | 把 chunk 从 4096 改 2048 重测；若错点跟着块边界移动即坐实 |
| `mmap /dev/mem failed: Operation not permitted` | 内核 `CONFIG_STRICT_DEVMEM` 或地址不在允许范围 | `zcat /proc/config.gz \| grep STRICT_DEVMEM`；改用 UIO/udmabuf |
| `pagemap: page not present` | 页还没 fault in（`memset` 之前就取 PFN） | 先 `memset` 再读 pagemap；确认 `CONFIG_PROC_PAGE_MONITOR=y` |
| 跑到一半地址变了 | 页被回收/迁移 | `mlock()`；或改用 `MAP_LOCKED` / 预留内存 |

---

## 5. 设计层面的三条铁律（写进 code review）

1. **一块 DMA 传输不许跨 4 KiB 页**（在"逐页映射非缓存别名"的方案里，跨页等于地址不连续）。
   `chunk` 取 4096 的约数即可；我们的实测 chunk 是 4096 B（1024 个 32-bit 样本），
   单块 117.7–118.6 µs。
2. **一致性策略只能有一个**：要么全程非缓存别名，要么全程 cached + 显式 sync。
   两种混用会产生"有时对有时错"的幽灵故障，而且现场无法复现。
3. **DMA 完成后必须先 `sync_for_cpu` 再读**；不要依赖"我 `usleep` 了 1 ms 应该写完了"。

---

## 6. 我们实测的完整时间线（可对照）

| 步骤 | 结果 | 证据 |
|---|---|---|
| 首轮（只 `cacheflush` L1） | 128000 样本中 **16 个错**，两段各 8 个，全 0 | `fpga/report/m3_compare_output.txt` |
| 加 2 MiB L2 冲刷 + 20 ms 等待 | `max_abs_diff 0`，`samples_diff_gt2 0` | `fpga/report/m3_compare_clean.txt` |
| 恒等比例 65536 复跑 | 输出 SHA == 输入 PCM16 SHA | `metrics/logs/pl_build/board_ratio_identity_20261025.log` |
| 另一比例 48000，**重新加载位流后** | 同样 `max_abs_diff 0` | `fpga/report/m3_compare_ratio48k.txt` |

> 附带教训：这次故障第一次出现时，我们以为"只有 16 个样本、而且是 0，可能是 RTL 复位没清"。
> 真正把它定位下来的是**错点长度恰好 32 B 且对齐**——先算清楚"错的形状"，比读代码快得多。
