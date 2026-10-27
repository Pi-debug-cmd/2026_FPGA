# Round12 FFT内核开销分解方案

任务 PL-20261027-01，2026-10-27，基准8ee3902。新增默认关闭的profile只读参数和stats只读JSON。事务/缓冲/精度/超时/位流不变，三段计时：copy_in包含头和DMA写屏障；device包含寄存器启动、设备等待与读屏障；copy_out为用户结果复制。只累计成功调用，mutex保护快照；默认profile=0不读时钟。

匹配5.15.0-xilinx module编译成功，SHA256 a882bc0bf3cadf7a6a89ceba3b640bd99b329db6be8eb75fe2e0a29dc1df447f。复现：build/build_world_fft_driver.sh <prepared-kernel-source> <matching-build>；板端静默rmmod/insmod world_fft_dma.ko profile=1后probe和两段文件，与profile=0输出逐字节对照，读取/sys/module/world_fft_dma/parameters/stats。计时本身有扰动，需比较开关。

内核CONFIG_ARM_DMA_MEM_BUFFERABLE=y，pgprot_dmacoherent已使用L_PTE_MT_BUFFERABLE，故不采用无收益的WRITE_COMBINE同义修改。200MHz或融合卸载需以本轮实测决定，不把软件阶段整体移植说成已经完成。
