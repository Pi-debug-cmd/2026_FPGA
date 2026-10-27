# CPU 与 PL 共享缓冲区：DMA 与缓存一致性

## 适用范围
CPU 与外部主设备（PL / PCIe / UIO）共享内存的数据搬运。与具体算法无关。

## 本仓库中的来源
- `src/kernel/pitch_dma_proxy.c`：内核字符设备驱动，`dmaengine` 收发双通道、
  `dma_addr_t` 缓冲地址、完成量同步、misc 设备接口、互斥锁保护 online/opened 状态
- `sim/generate_dma_board_vectors.py` / `generate_dma_control_vectors.py`：DMA 与寄存器测试向量

## 使用方法
1. 缓冲区优先用 `dma_alloc_coherent`；必须用普通页时，在**每次**提交 DMA 前后做 cache 维护。
2. 传输完成用完成量阻塞等待，不用轮询延时。
3. 驱动侧对 `online/opened` 加锁，保证只有一路使用者。

## 典型故障与判读
- **现象**：DMA 后部分样本恒为 0，且**只在首次传输出现**
- **判读**：地址未按 cache line 对齐导致的边界写回；把缓冲区按 32/64 字节对齐后复测
- **排除法**：先传已知常量向量（全 1），确认是"数据被改写"还是"未写入"

## 失效条件
- 平台为一致性互联（ACE/CCI）且映射为 non-cacheable 时，本方法仍安全但非必需

## 复用场景
任何 CPU + 外部主设备的共享内存；换平台只改分配函数与对齐要求。
