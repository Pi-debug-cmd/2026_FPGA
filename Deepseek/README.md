# 工程交接：把这条链路在 Zynq-7020 上跑起来

## 目标
让板子完成"男声 → 目标女声"的实时转换，并能从喇叭听到正确的声音。

## 现状（一句话）
转换算法已验证正确（板端输出与电脑参考 corr 0.99999999）；**唯一未通的是模拟输出**：aplay 能跑、无报错，但喇叭里是噪声。

## 已确认的事实
- 硬件固定格式：S24_LE / 32000 Hz / 2ch（`/proc/asound/card0/pcm0p/sub0/hw_params` 可查）
- 采集设备名是 `capture`（不是 default）；hw:0,0 播放、hw:0,1 采集
- 每次打开音频设备都打印：`wm8960 0-001a: slave mode, but proceeding with no clock configuration`
- 直接播放未转换的原始 PCM 同样是噪声 → 与转换算法无关，问题在 WM8960 时钟/路由
- 板子串口 COM8 / 115200 / root:root；上传超过约 30 字符会偶发字符重复，必须分片发送

## 首要任务（按顺序）
1. 修 WM8960 时钟配置（设备树 clocks / dai 配置，重新生成 dtb）——这是出声的关键
2. 确认麦克风接入的输入通道（LINPUT1/2/3）与 MICBIAS 是否提供
3. 修 PL 路径的内存碎片问题（`pl_stft: no 3 physically contiguous pages`）

## 板上命令速查
见 `STATUS_AND_ISSUES.md` 第三节。

## 目录说明
- `host/`  板端 C 程序源码、构建脚本、模型 blob（`host/model/`）
- `fpga/`  RTL、Tcl、位流（`fpga/stft/` 为当前入链版本）
- `docs/`  架构、接口、硬件接线、工具链说明
- `report/` 设计报告与实测数据

## 纪律
- 修改前先在串口确认 `cat /sys/class/fpga_manager/fpga0/state` = operating
- 音频测试前 `/etc/init.d/world-voice stop`
- 不覆盖板上现有的可用二进制，新增文件加后缀
