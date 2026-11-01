# 板级启动与运行时校验（Board Bringup & Runtime Probe）

## 适用范围
Zynq-7000 / Zynq UltraScale+ 平台上"位流已加载但行为不对"的定位。不依赖具体算法。

## 本仓库中的来源
- `board/bringup.md`：上板步骤与已知问题
- `board/audio_path_probe.sh`：音频通路探测
- `board/check_world_live_runtime.py`：运行时状态检查
- `board/check_control_python.py`：控制面寄存器读取校验

## 使用方法
1. 先确认位流状态与驱动绑定，再探测数据通路。
2. 每一层（位流 / 驱动 / 时钟 / 通路）单独出结论，不跳层。
3. 探测脚本只读不写，避免改变状态。

## 失效条件
- 位流本身与硬件不匹配
- 设备树未描述该外设

## 复用场景
任何"PL 加载成功但外设不工作"的板级调试；换板卡只需改设备名与寄存器地址。

## 文件
见本目录 `probe_checklist.md`
