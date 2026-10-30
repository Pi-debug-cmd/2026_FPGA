# Round13 WORLD整链PL融合迁移方案

任务 `PL-20261027-01`，日期 2026-10-27，基准 `9eb5509`。用户要求“能放PL就放PL，能全放更好”。Round12 已证明逐FFT ioctl边界的内核成本约31%回读、62%设备事务，继续增加单个FFT频率或做小幅PS循环优化不能达到高实时目标。因此本轮定义帧级融合迁移方案。

## 目标边界

PS保留ALSA/音频DMA、环形队列、线程调度、停止/故障处理和最终PCM封装。PL连续接收输入，保留原160ms历史与40ms未来上下文，以4帧（40ms）及F0/目标参数为计算批次，完成固定窗口和频域计算，返回连续输出块；中间FFT、谱、非周期参数、exp和最小相位/合成缓存不返回PS。先保持WORLD v23的16 kHz、10 ms分析帧、1024点CheapTrick和513-bin D4C输出（D4C内部FFT按原公式）及当前128样本输出块，不改变参数和随机种子契约。

## 分层落地

1. **Frame front-end（第一实现）**：AXI4-Stream持续输入（每批新增4×160样本，核内保存历史和未来上下文）、帧F0和模式；PL完成窗函数、1024点r2c、功率谱/对数谱、频点映射和目标谱变换；输出513点float或定点谱。用同一输入帧的C++ golden model逐bin对照，先达到PCM16最大误差门。
2. **D4C batch（第二实现）**：把D4C的固定3 kHz间隔粗粒度统计、群延迟平滑和aperiodicity插值放入同一帧事务。可变F0窗口先用最大窗口+边界掩码，避免动态内存；随机激励必须复现原WORLD RandnState算法、种子与消费顺序，不用不同LFSR替代；初期可先由PS提供原序列，确保回归可重放。
3. **Synthesis batch（第三实现）**：把当前 `synthesisrealtime.cpp` 的anchor最小相位滤波、脉冲位置、噪声/声门激励和overlap-add状态放入PL。PL按原v23维护anchor窗口及跨批次overlap-add状态（非仅4帧），按128样本输出；PS不再回读每个513-bin中间数组。
4. **融合DMA（最终实现）**：单个HP事务覆盖输入、参数、输出环形缓冲，使用双缓冲和中断/门限；一次事务覆盖40 ms，目标是把现有3279次/5秒的边界降到约127次，减少实测约0.19 s的prepare/unpack和中间传输等待；融合后的实际收益仍需板测。

## 数值和资源门

每层都必须与当前v23逐字节/PCM16回归：最大误差≤3（现有PL exp组合门），SNR≥75 dB，exp fallback=0，零削顶；任何下降先停止融合。每层独立综合和布局布线，记录LUT/FF/BRAM/DSP/WNS/WHS。当前compact FFT整机为17255 LUT、29197 FF、24.5 BRAM、69 DSP，余量不能直接视为整链可容纳；D4C和合成的乘加、三角/对数/指数近似需分别给出预算。100 MHz先签核，若资源允许再评估200 MHz，不以改频率替代融合接口。

## 融合实现顺序补充

源码复核后，首个融合硬件原型选定最小相位滤波器生成（镜像谱→两次FFT→倒谱lifter→exp/cos/sin），其接口比完整D4C更明确，先做C-sim和资源预算。上文Frame front-end不是CheapTrick完整等价实现：功率谱后还需要原WORLD平滑等步骤，不以普通STFT代替。完整分析和合成仍是目标。1024/2048为现有IP尺寸，D4C内部FFT尺寸必须按原源码公式保留，不从输出513-bin推断其内部点数。

## 后续入口（待写代码）

`src/rtl/synth_offload/world_frame_frontend_hls.cpp`（HLS C-sim与综合）、`sim/world_frame_frontend_golden.py`（NumPy/固定点对照）、`build/create_world_exp_20261027.tcl fft`的独立HP端口。第一阶段不切板、不停用原v23；通过C-sim、RTL随机背压和整机资源门后，才做静默文件回归。任何现场录放仍需当轮准备确认。

## 当前限制

完整WORLD并非直接把C++搬进PL：D4C含可变F0窗口、排序/平滑和随机激励，合成含状态机、脉冲位置和overlap-add。必须先固定接口与数值近似，再逐层替换；“全放PL”是目标架构，尚未是板端结论。
