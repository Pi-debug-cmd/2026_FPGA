# dma_cache_coherency — 用户态 DMA 缓存一致性封装 + 出错定位清单

> 一句话：把「AXI DMA 搬数据」这件事封装成一个**不会因为缓存而偶发清零**的缓冲区 API，
> 并附一份把"少了 16 个样本"变成"脏 cache line 回写"的**诊断清单**。

## 1. 为什么值得单独做成 skill

Zynq-7020 上 AXI **HP 口不是 cache-coherent 口**（只有 ACP 是），
而 PetaLinux 板端最常见的写法是 `/dev/mem` + `mmap` —— 这条路上，
"程序能跑"和"数据正确"是两件独立的事：

- 我们第一版端到端比对：128000 个样本里 **16 个错**，两段、每段正好 8 个、值全 0；
- 同一个二进制再跑一次，**结果完全正确**；
- 只加 `cacheflush()`（ARM 私有 syscall）**没用**——它只清 L1，PL310 L2 不归它管；
- 加 "2 MiB 冲刷（4×L2）+ 20 ms 等待" 之后 `max_abs_diff = 0`。

这类 bug 的识别成本远高于修复成本，所以它值得一个可复用的封装 + 一份可执行的判读表。

## 2. 目录

```
dma_cache_coherency/
├── dmabuf.h / dmabuf.c      # 缓冲区 API：非缓存别名（默认）/ cached+sync（备选）
├── dma_roundtrip.c          # 30 秒自检：pattern → DMA → 比较，输出"错的形状"
├── diag_checklist.md        # ★ 现象→根因→定位命令→修复（本 skill 的核心）
├── bin/dma_roundtrip        # 已交叉编译的静态 ARM 可执行（SHA 见 results.md）
└── example/
    └── run_check.sh         # 板上一条命令跑完自检 + 打印判读结论
```

## 3. API 速览

```c
dma_buf b;
dma_buf_alloc(&b, bytes, DMA_COHERENT_UNCACHED);   /* 推荐 */
/* CPU 只通过 dma_buf_cpu(&b, off) 读写；off 必须按页对齐切块 */
memcpy(dma_buf_cpu(&b, 0), src, n);
dma_sync_for_device(&b);                            /* 非缓存模式下是 barrier */
transfer(dma_buf_phys(&b, 0), ...);                 /* 物理地址给 DMA */
dma_sync_for_cpu(&b);                               /* 之后再读 */
dma_buf_free(&b);
```

- `dma_buf_alloc` 内部做：匿名页 → `mlock` → `/proc/self/pagemap` 取 PFN →
  `/dev/mem` 逐页映射非缓存别名 → `cacheflush` + L2 冲刷（把初始化脏行赶出去）。
- 约束在运行时检查：单次搬运不许跨 4 KiB 页（跨页在别名方案里地址不连续）。
- `DMA_COHERENT_FLUSH` 是**best-effort** 备选（有些内核禁 `/dev/mem`）：
  它靠"冲刷 ≥4 倍 L2 后等 20 ms"来保证没有脏行残留，属于**时序假设**，不推荐。

## 4. 快速开始（板上）

```sh
# PL 必须先配成直通模式（ratio_q16 = 65536）
./dma_roundtrip --dma 0x40400000 --ratio-addr 0x41200000 --ratio 65536 \
                --words 128000 --chunk 4096 --pattern ramp --repeat 5 --realloc
```

期望：每行 `"mismatch":0`，退出码 0。
若出现 `zero_runs_32B_aligned>0` 且 `max_zero_run:8` —— 直接翻 `diag_checklist.md` §1。

## 5. 失效条件（什么时候这套封装不适用）

- **需要超过 2 MiB 单缓冲**：本实现逐页映射，页数上限 64（256 KiB 默认页表项，
  可改 `DMABUF_MAX_PAGES`）；大缓冲请走 CMA/reserved-memory。
- **内核禁 `/dev/mem`**（`CONFIG_STRICT_DEVMEM` / `CONFIG_IO_STRICT_DEVMEM`）：
  只能用 `DMA_COHERENT_FLUSH`（best-effort），或改 UIO / `udmabuf` / 自写驱动。
- **非 ARM32 / 非 PL310 L2**：`cacheflush` syscall 号与 L2 尺寸都不同，
  `dma_l2_scrub(2 MiB)` 这个常数必须按实际 L2 改（A53 的 L2 通常 512 KiB–1 MiB）。
- **ACP 口 + `dma-coherent` 设备树属性**：硬件已经保证一致性，本封装的多余 flush 只会变慢，
  但不影响正确性。
- **64 位物理地址**：结构体里 `uint32_t` 写 DMA 地址（AXI DMA 7.1 simple mode 的限制），
  ZynqMP 上要改成 64 位寄存器。

## 6. 换题目 / 换板卡还能怎么用

- **换一个 PL 加速器**（图像、CNN、FFT 都行）：`dmabuf` 与业务无关，改的只是
  "搬多少、搬到哪"；`dma_roundtrip` 只在 PL 直通模式下用，其它 IP 可以先用
  "写 A 读 A"的最小 IP 验通路。
- **换一块 Zynq-7000 板（Zybo/PYNQ-Z1/自定义）**：只改 DMA/GPIO 基地址；
  L2 尺寸若不同，改 `L2_SWEEP_BYTES`。
- **换到 ZynqMP（UltraScale+）**：把 `cacheflush` 换成 `dc civac` 的 `__builtin___clear_cache`
  或 UIO+`dma-coherent`，诊断清单的判读逻辑（32 B/64 B 对齐零段）完全复用。
- **PYNQ 场景**：`pynq.allocate()` 已经用了 CMA + `dma_alloc_coherent`，
  但**一旦你自己 `numpy.zeros()` 再喂给 DMA，就又会踩这个坑**；
  本清单可以直接当"为什么我的 PYNQ DMA 结果偶尔全 0"的排查流程。
- **任何"CPU 与外部 master 共享内存"的场合**（PCIe BAR、USB gadget、网卡 ring）：
  §1 的"32/64 字节对齐零段 + 只在第一次出现"这个指纹是通用的。

## 7. 已验证结果

见 `results.md`：`max_abs_diff = 0`（128000/128000），恒等比例下输出 SHA == 输入 SHA，
三个比例（65536 / 48000 / 86856）各自复现；`dma_roundtrip` 已用
`arm-linux-gnueabihf-gcc -Wall -Wextra` 编译通过（静态，511,928 B）。
