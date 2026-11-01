# PL-20261027-01 Round28：持久资产安装与回读

## 结论

**ACCEPTED（持久安装门，候选仍受 INSTALL_GUARD 禁用）。** 版本化 rootfs release、factory init 备份、新包装 init、控制工具和 `/boot/world_pl` 资产已经安装并逐件从目标位置回读 SHA。原厂 `zynq7020.bit`、`uEnv.txt`、`boot.scr` 和 v23 哈希全部保持不变；`BOOT.BIN` 未覆盖。FAT 选择文件为 `DISABLE=INSTALL_GUARD`，所以本轮没有切换 FPGA、插入候选 module 或启动新采录放。

## 安装结果

- `/opt/world_voice_pl/releases/20261029_round27`：版本化 runtime、module、supervisor、switch 和 manifest；`/opt/world_voice_pl/current` 指向该 release。
- `/etc/init.d/world-voice.factory`：原 init 精确备份，SHA `067ba4d2...2447`。
- `/etc/init.d/world-voice`：新包装器，SHA `211392ce...499`；原 `/etc/rc5.d/S99world-voice` 链接不变，仍指向该入口。
- `/usr/sbin/world-pl-control`：SHA `a097d330...dd6`。
- `/boot/world_pl/world_minphase_swap.bin.gz`：SHA `6a7fec99...8d98`；manifest 和 recovery JSON 已安装。
- `/boot/world_pl/DISABLE` 内容为 `INSTALL_GUARD`，当前启动选择明确为 factory v23。

目标位置执行 rootfs manifest 6/6、boot manifest 1/1 均 `OK`。安装器输出：`WORLD_MINPHASE_INSTALL_OK active=factory guard=INSTALL_GUARD boot_originals_unchanged=1`。

## 原厂基线回读

| 文件 | SHA-256 |
|---|---|
| `/boot/bit/zynq7020.bit` | `16cb36f7161935896615ad12b000597088a6a9745856611162f1c44a51f82a61` |
| `/boot/uEnv.txt` | `e211c7f8b8034c02c9035d71c05237607f09efeec272ad9d9c774788431c53c2` |
| `/boot/boot.scr` | `7702e40c863bb4d73b561ad9dd112537fd4560515286e9a3f5aebb133a6383f8` |
| `/opt/world_voice/world_budget_v23` | `f12da25e93a520b7f5255ce952a3cb9b5d1bbca474133b1bc529d8c8e18349b7` |

## 传输与安全状态

首次 ARM runtime 串口传输在约 97% 时被原厂 v23 的周期性音频重开日志打断；上传器未接受未校验文件。随后停止原厂实时服务，确认双 PCM closed，并从已核验 encoded offset `2,613,248 / 2,686,482` 续传，最终完整 runtime SHA 通过。其余文件全部逐件验证。

安装后：FPGA `operating`（原厂 bit），双 PCM closed，kernel taint 0，无 `world_minphase` module。原厂服务因上传静默化而保持 stopped；没有为了本轮重新开启采录放。

## 边界与下一步

当前已经具备持久部署和 A/B 回退，但默认仍由 INSTALL_GUARD 选择 factory。下一轮删除 guard 并启动包装服务时会自动开始提示、采集和播放，按项目规则仍需当次操作者明确准备；用户已决定不做稳定性与提示音可闻验收。首次 enable 后只验证启动状态、candidate/module/backend 计数和削顶遥测；如任何启动/runtime 门失败，服务应自动写 DISABLE 并回退 factory。
