# PL-20261027-01 Round19：最小相位 PL 板端软件闭环

## 结论

Round18 的融合最小相位硬件已具备可加载且可调用的 Linux 软件链：确定性 FPGA Manager 载荷、coherent DMA 内核模块、WORLD `GetMinimumPhaseSpectrum` 包装和 24 例静默 DMA 探针均构建通过。模块与现有板端内核匹配为 `5.15.0-xilinx`/ARMv7；用户态主程序和探针均为 32-bit ARM 静态 ELF。

本轮没有加载板卡，不能把“构建通过”写成板端数值、实时或音质通过。下一轮必须先用 24 例静默向量验证 MMIO、HP2 DMA 和数值，再验证恢复原厂 bit/v23。

## 软件契约

- 设备：`/dev/world_minphase`，权限 `0600`，单实例 mutex 串行。
- ioctl：513 个 float32 log-spectrum 输入，513+513 个 float32 复数滤波器输出，共 6,156 bytes。
- DMA：三段 coherent 缓冲，32-bit mask，经 HP2；不把用户页直接交给 PL。
- 寄存器：控制 `0x43C70000`，三指针位于 `0x43C80000 + 0x10/0x1c/0x28`。
- 完成条件：轮询 `ap_done`，20 ms 硬超时；发生超时后模块进入 failed 状态，拒绝静默 CPU 回退。
- WORLD 包装：仅 `WORLD_MINPHASE=pl` 打开设备；未设置或 `cpu` 时保持原 WORLD。非 1024 FFT 明确回退并计数。
- 主程序可同时设置 `WORLD_EXP=pl`，因此保留既有 complex-exp PL 路径并新增最小相位融合路径。

## 构建与验证

```powershell
$world='C:/Users/World/Desktop/2026_FPGA/build/generated/world_source_v035/pyworld-0.3.5/lib/World'
powershell -File build/build_world_exp.ps1 -WorldRoot $world -Target arm -MinphasePl
python build/package_world_minphase.py --project D:/wpl_20261029_full/m
wsl -e sh -lc "sh build/build_world_minphase_driver.sh /var/tmp/2026_fpga_kernel_20261010/source/linux-ebf-xilinx-v2022.2 /var/tmp/2026_fpga_kernel_20261010/build"
```

- 主程序 SHA-256：`2dea4725867974f20319f5ea418aa67258aede0bcfd43e72fb1cf2d39559f438`，1,988,692 bytes。
- 24 例探针 SHA-256：`664bc0819b5c76791761b5ac6a5a7af61e42a973ef4c55c6cca054c7131723f6`，566,456 bytes。
- 模块 SHA-256：`fbbe531f16189fb720a487fbcfa2d78ab1d08836488c93850e7a8480fbc31f62`，10,124 bytes。
- 原始 bin SHA-256 与 Round18 一致：`2e8517d9d126261fd397ec76e3209b111d9cee232d6374bdc9bb099473d79117`。
- 字内换序 bin SHA-256：`1bc4b3f8f5e5f1b722b0772b9aad23af3c60579dc3c81c44c8d86b408c429373`。
- 固定 mtime 的 gzip SHA-256：`6a7fec9987d31c5f803b79b1bb8e115dca9fda0dfc278b8f462d60562b628d98`，536,768 bytes；连续两次生成哈希一致。
- ARM 符号检查存在 `__wrap_GetMinimumPhaseSpectrum`；HLS 导出头再次确认指针偏移为 `0x10/0x1c/0x28`。

首次探针构建因上游 WORLD `fft.cpp` 的聚合初始化告警在 `-Werror` 下停止；只对该上游告警增加与既有 FFT 探针相同的 `-Wno-missing-field-initializers` 后通过。第一次在 sandbox 内向 D 盘工程写包被权限阻止，获准后生成；这不是代码或数值失败。

## 限制与下一步

- 尚未执行板端 ioctl，24 例的板上 relative-L2 结果仍为空。
- 尚未量测实际 DMA/核耗时及整条 v23 文件转换的 RTF。
- 本轮未录音、播放或试听，未修改启动分区。
- 下一轮只做可恢复的静默板测：核对当前原厂状态，临时加载 candidate，运行 24 例探针和文件转换对照，然后恢复原厂 bit/v23 并核对 PCM、服务和内核状态。
