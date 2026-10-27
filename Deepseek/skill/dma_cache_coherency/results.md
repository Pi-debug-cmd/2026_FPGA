# 已验证的复用结果 — dma_cache_coherency

## 1. 环境

| 项 | 值 |
|---|---|
| 板卡 | 野火皓月 Zynq-7020，`xc7z020clg400-2`，Cortex-A9 ×2，PL310 L2 512 KB |
| 镜像 | PetaLinux 2022.2，`5.15.0-xilinx` |
| PL | `audio_pitch_dma`（AXI DMA simple mode + 变调核），DMA base `0x40400000` |
| 缓冲区 | 2 × 匿名页，经 `/proc/self/pagemap` 取 PFN，`/dev/mem` 映射为非缓存别名 |
| 单块 | 1024 × 32-bit = 4 KiB；实测 117.7–118.6 µs/块 |
| 日期 | 2026-10-25（首次失败与修复），2026-10-26（重新编译核对） |

## 2. 故障与修复（原始证据）

| 轮次 | 处理 | 128000 样本结果 | 证据文件 |
|---|---|---|---|
| 第 1 轮 | 仅 `cacheflush`(L1) | **16 个样本错**，两段各 8 个，全 0（`samples_diff_gt2=16`） | `fpga/report/m3_compare_output.txt` |
| 第 2 轮 | `cacheflush` + 2 MiB L2 冲刷 + `usleep(20 ms)` | `max_abs_diff 0`、`samples_diff_gt0 0`、`samples_diff_gt2 0` | `fpga/report/m3_compare_clean.txt` |
| 第 3 轮 | 恒等比例 65536 | 输出 SHA == 输入 PCM16 SHA（`380d6dbb…`） | `metrics/logs/pl_build/board_ratio_identity_20261025.log` |
| 第 4 轮 | 比例 48000，**重新加载位流后** | 同样 `max_abs_diff 0` / `VERDICT PASS` | `fpga/report/m3_compare_ratio48k.txt` |

第 1 轮的关键判读：错点**恰好 32 B（8 × 16-bit）且在 32 B 边界上**、
只在首轮出现、且第二次运行不复现 —— 这三条同时成立时，可以直接判定为
"cached 别名上的脏零行在 DMA 之后回写"，不需要再去读 RTL。

## 3. 吞吐（同一路径，供预算参考）

| 指标 | 数值 |
|---|---|
| 4 s / 128000 样本总耗时（含文件 I/O 与 PCM 打包） | 31.19 ms |
| 纯 DMA 往返 / 1024 样本 | 117.7–118.6 µs |
| 样本吞吐 | 4.10 M 样本/s（≈128× 实时，32 kHz） |
| 恒等旁路（ratio=65536） | 6.49 M 样本/s（25.8 µs/块） |

## 4. 复现性（本 skill 的代码级证明）

- `dmabuf.c` + `dma_roundtrip.c` 用 `arm-linux-gnueabihf-gcc -static -O2 -Wall -Wextra`
  编译通过，**零警告**，产物 511,928 B，SHA-256 `fa20a4e2f8832fff…`。
- 同一工具链重编译 `pitch_dma_mem.c`，产物 SHA-256 `fe312bb177a02011…`
  与**当时在板上跑出上述结果的二进制逐字节相同** —— 说明"源码 → 板上行为"这条链可复现，
  不是某个手工改过的临时产物。

## 5. 未覆盖

- 未测 `DMA_COHERENT_FLUSH` 模式在**长时间（>10 min）连续跑**下是否仍无脏行残留；
  该模式本身有时序假设，正式结论只承认 `UNCACHED` 模式。
- 未在 `CONFIG_STRICT_DEVMEM=y` 的内核上试过（本板该选项关闭）。
- 未测 ACP 口（`dma-coherent`）路径，因此"硬件一致时本封装是否只是多余开销"未量化。
