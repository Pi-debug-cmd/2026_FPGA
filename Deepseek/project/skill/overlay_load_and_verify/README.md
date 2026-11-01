# overlay_load_and_verify — 通用 PL Overlay 加载 / 回读校验 / 回滚

> 一句话：把"把位流塞进 Zynq 并确认它真的活了"这件事，从一次性 shell 操作变成
> **有日志、有前置回滚、有寄存器级验收**的可重复流程；换一块板/换一个 overlay 只改 JSON 和命令行参数。

## 1. 它解决什么问题

PL 加载失败的四种真实形态，本工具逐条对上：

| 失败形态 | 现象 | 本工具的处理 |
|---|---|---|
| 镜像格式错 | `fpga_manager` 写 firmware 后 state 仍是 `operating`，dmesg 无输出 | 加载前校验 `0x665599aa` 同步字（Zynq 要求每 4 字节反转），**在写 firmware 之前**就报错 |
| 旧 PL 消费者还占着设备 | 加载"成功"但新 IP 的驱动 probe 失败、`ioremap failed (-22)` | 按"上层→底层"顺序 unbind 一份**外部给的**设备清单，每步落盘 |
| 加载到一半板子挂死 | 会话断，现场无人知道加载到了哪一步 | 每步先写 journal（`switch_state.json`）再执行；`panic=10` 让 oops 自动重启回原厂位流 |
| 位流对了但寄存器没生效 | 无报错、数据全 0 | 寄存器回读：reset 值 + 写入值 + 恢复值三重比对，失败即非零退出 |

## 2. 目录

```
overlay_load_and_verify/
├── overlay.py              # 加载器：record → quiesce → unbind → load → rebind → restore
├── regtool.py              # 寄存器表驱动验收（需要 python 有 mmap）
├── regtool.c               # 同一件事的静态 C 版（板端 python 无 mmap 时用这个）
├── example/
│   ├── register_map.json   # 本项目 AXI GPIO 的寄存器表（可直接改成别的 IP）
│   ├── consumers.txt       # 需要 unbind 的设备清单
│   └── run_on_board.sh     # 一条命令走完：加载 → 寄存器验收 → 打印证据
└── results.md              # 本项目实测记录（含失败对照）
```

## 3. 快速开始

主机侧（生成 Zynq 可加载镜像 + 回滚镜像）：

```bash
python3 make_swap.py zynq_wrapper.bin overlay_swap.bin      # 每 4 字节反转 + gzip
# 板上：从启动分区只读地抽出原厂位流，做成回滚镜像
python3 prepare_recovery.py /tmp/pl_x
```

板端（root）：

```bash
cd /tmp/pl_x
python3 overlay.py \
  --image /tmp/pl_x/overlay_swap.bin \
  --run-dir /tmp/pl_x \
  --consumers consumers.txt \
  --rebind "41600000.i2c 43c20000.axi_dynclk 43c50000.i2s_receiver 43c60000.i2s_transmitter 43c40000.audio_formatter xlnx_snd_card.0.auto" \
  --pause music-button-listener

python3 regtool.py example/register_map.json --json /tmp/pl_x/reg_check.json
# 或（板端 python 无 mmap 时）
./regtool --base 0x41200000 --check 0x00:18:86856,65536,131072,32768,86856 --check 0x08:1:0,1

# 一条命令回滚到原厂位流
python3 overlay.py --image /tmp/pl_x/factory_restore_swap.bin --run-dir /tmp/pl_x \
  --rollback-to /tmp/pl_x/factory_restore_swap.bin
```

## 4. 设计要点（都是踩过的坑换来的）

1. **镜像必须 `+4 byte swap`**：Vivado `.bin` 的 32 位配置字是大端，Zynq PCAP 要小端。
   校验方式不是看文件名，而是在前 256 字节里找 `66 55 99 aa`；找不到就直接拒绝，
   否则你会得到一次"无声的成功"。
2. **unbind 顺序 = 上层消费者先死，叶子后死**。反了会在 `unbind` 上卡住或 oops。
   清单必须由调用方给（不同底板的 PL 外设完全不同），工具不内置任何板级常量。
3. **加载期间 `panic=10`**：万一旧消费者在解绑后又碰了已消失的地址，内核 oops 会在 10 s 后
   重启，U-Boot 重新加载原厂位流——这是最可靠的自动回滚。
4. **`firmware_class.path` 用完必须恢复**：否则之后任何 `request_firmware` 都会去你的临时目录找，
   表现为"别的驱动突然找不到固件"。
5. **寄存器 reset 值优先于读写测试**：如果 reset 值与 BD 里的 `C_DOUT_DEFAULT` 不一致，
   说明位流和你以为的不是同一版，或者有人在你之前写过——此时后面的读写"通过"也没有意义。
   `regtool` 对这种情况给出专门的 `diagnosis` 字段。
6. **width/mask 必须写进寄存器表**：18 位寄存器的上 14 位读回来是什么，各 IP 不一样；
   用 mask 比较才不会被无关位搞成假失败/假通过。

## 5. 失效条件（什么时候不要用它）

- **不是 Zynq-7000 的 `fpga_manager` 路径**（如 UltraScale+ 的 `dfx-mgr`、Intel 的 `partial reconfiguration`）：
  加载那一段要换实现，journal / 寄存器验收 / 回滚思路可以照搬。
- **需要 Partial Reconfiguration（动态区）**：本工具换的是整片 PL，会复位所有 PL 外设。
- **安全启动 / 位流加密**：镜像不是明文 `.bin` 时同步字校验不成立。
- **没有 `/sys/bus/platform/devices` 的老内核（<3.x）**：unbind 那段要改成 `driver/unbind` 的旧路径。
- **板上 python 没有 `mmap`**：`regtool.py` 用不了，必须用 `regtool.c`（我们就是这种情况）。

## 6. 换题目 / 换板卡还能怎么用

- **换一个 overlay（同一个 Zynq 板）**：只改 `--consumers`、`--rebind` 和 `register_map.json`，
  三个文件都不用动。本项目从"视频/GPIO 底板设计"切到"音频变调核"就是只改了清单。
- **换一块 Zynq-7000 板（如 Zybo / PYNQ-Z1 / 自定义底板）**：`overlay.py` 不含任何板级常量，
  换的是 `consumers.txt` + 回滚镜像的生成路径；寄存器验收完全复用。
- **任何"先加载、再回读确认"的硬件实验**（不止 FPGA）：把 `regtool` 换成 I2C/SPI 读写即可，
  journal + reset 值优先 + 非零退出这套骨架不变。
- **PYNQ 场景**：`pynq.Overlay()` 已经封装了加载，但**没有回滚、没有消费者解绑、没有 reset 值校验**；
  本工具可以只取 `regtool` + `results.md` 的验收表，作为 Overlay 的"上线前自检"。

## 7. 已验证结果

见 `results.md`：2026-10-25，xc7z020clg400-2 + PetaLinux 2022.2，
`fpga_manager operating → operating`、GPIO 5/5 组读写全对、回滚镜像 SHA 与 2026-10-10 记录一致、
DMA 端到端 128000 样本 bit-exact。
