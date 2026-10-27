# 已验证的复用结果 — overlay_load_and_verify

## 1. 环境

| 项 | 值 |
|---|---|
| 板卡 | 野火皓月 Zynq-7020，`xc7z020clg400-2` |
| 镜像 | PetaLinux 2022.2，内核 `5.15.0-xilinx`，双核 A9，1 GB |
| 主机工具 | Vivado 2018.3（SW Build 2405991），Linaro GCC 7.3.1 |
| 串口 | COM8 / 115200 / root（独占） |
| 日期 | 2026-10-25 |
| 位流 | `audio_pitch.bit` 4,045,672 B / `audio_pitch_dma_2018_swap.bin` 4,045,564 B |

## 2. 加载验收（M2）

原始日志：`metrics/logs/pl_build/board_pl_load_20261025.log`、`board_gpio_check2_20261025.log`。

| 检查 | 实测 | 判定 |
|---|---|---|
| 加载前 `fpga_manager/fpga0/state` | `operating` | 记录在 journal |
| 加载后 state | `operating` | 通过 |
| dmesg | `fpga_manager fpga0: writing audio_pitch_dma_2018_swap.bin to Xilinx Zynq FPGA Manager`，无 oops | 通过 |
| unbind 的旧 PL 消费者 | 18 个全部 `unbound` | 通过 |
| 重新绑定的音频驱动 | 6 个（i2c/dynclk/i2s rx/tx/formatter/snd_card） | 通过，`/dev/snd/controlC0` 存在 |
| 镜像 SHA 一致性（主机 ↔ 板端） | `8aedb87d…` 两侧一致；gzip 后 332,294 B / `faf6c271…` | 通过 |

## 3. 寄存器回读（M2）

板上精简 python **没有 mmap 模块**，所以正式证据由静态 C 版 `regtool`（源自 `gpio_check.c`）产生：

```json
{"base":"0x41200000","initial":86856,
 "cases":[{"wrote":86856,"read":86856,"ok":true},
          {"wrote":65536,"read":65536,"ok":true},
          {"wrote":131072,"read":131072,"ok":true},
          {"wrote":32768,"read":32768,"ok":true},
          {"wrote":86856,"read":86856,"ok":true}],
 "ch2":{"reset_read":0,"run_read":1},"restored":86856,"all_ok":true}
```

- `initial = 86856` 证明 BD 里 `C_DOUT_DEFAULT = 0x15348` 生效：**位流一加载就是原固定比例行为**，
  没有"加载完还要写一次才对"的隐藏依赖。
- 五个值（含 65536 恒等、131072 双倍）全部精确回读 → AXI-Lite 通路与地址译码正确。
- 该表已固化进 `example/register_map.json`，`regtool.py` / `regtool` 都能直接复跑。

## 4. 回滚

- 用 `prepare_recovery.py` 只读解析启动分区 `/boot/bit/zynq7020.bit`（SHA `16cb36f7…`），
  生成 `factory_restore_swap.bin`（SHA `af275946…`）。
- 该 SHA 与 2026-10-10 的历史记录**完全一致**，说明"原厂位流 + 交换算法"两者都没漂移，
  回滚镜像可用。
- 加载全程 `panic=10`，boot 分区从未写入（`/boot/bit/zynq7020.bit` SHA 加载前后一致）。

## 5. 这条 skill 在本项目之外的复用

- 本项目的 PL 侧一共换过两次设计（2026-10-10 视频/GPIO 底板 → 2026-10-25 音频变调核），
  **`overlay.py` 两个版本一行没改**，只换了 `consumers.txt` 和 `--rebind` 列表。
- 寄存器验收脚本被 `dma_cache_coherency` 的跑数流程直接调用（加载后先验寄存器再跑 DMA），
  两个 skill 是串联使用的。

## 6. 已知未覆盖

- 未测"加载中断电"的恢复路径（只做了 oops→panic→重启 的推演，没有实测断电）。
- 未在 PYNQ 镜像上跑过（本板是 PetaLinux）；PYNQ 的 `pynq.Overlay` 与 `fpga_manager` 共用同一接口，
  预计可用，但属于**未验证**。
