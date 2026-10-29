# PL-20261027-01 Round27：开机自动 PL 与失败回退方案构建

## 结论

**ACCEPTED（部署方案与故障注入门，尚未持久安装）。** 按用户决定跳过稳定性和提示音可闻测试，已完成输出削顶修正、开机自动切换 candidate、运行失败回退 factory v23、FAT `DISABLE` 恢复开关和版本化资产清单。板上 `/tmp` 的 BusyBox shell 语法检查及两项无声故障注入通过，未切换 FPGA、未打开新音频流、未写启动分区。

## 方案

- U-Boot 仍加载原厂 `/boot/bit/zynq7020.bit`，不覆盖 `BOOT.BIN`、`boot.scr`、`uEnv.txt` 或原厂 bit。
- 启动分区只新增 `/boot/world_pl/`：candidate 的 FPGA Manager gzip 载荷、逐件 SHA、恢复说明和可由电脑/串口创建的 `DISABLE` 开关。
- 原 `/etc/init.d/world-voice` 安装时备份为 `/etc/init.d/world-voice.factory`；现有 `/etc/rc5.d/S99world-voice` 不变，由新包装器接管。
- 默认无 `DISABLE`：开机先由原厂 bit 安全启动，包装器停止 v23，校验资产，生成恢复镜像，切换 candidate、插入 `world_minphase_dma.ko` 并启动 600 秒循环实时链。
- 任一资产、切换、module、device 或 runtime 失败：写入 FAT `DISABLE`，恢复原厂 bit并启动 v23；下一次启动直接绕过 candidate，避免重复失败。
- `world-pl-control enable|disable|status` 提供显式 A/B 选择。
- `world_exp_switch.py` 新增 `WORLD_FACTORY_SERVICE` 覆盖，持久服务使用备份的 factory init，避免包装器递归调用自身；原临时测试默认行为不变。

## 削顶修正

持久服务和监督器默认输出 Q16 从 `49152`（0.75）降为 `16384`（0.25）。Round25 输出 peak `2.423787389` 按同一波形线性折算为 `0.807929130`，留出约 1.85 dB 峰值余量。用户明确不要求本轮稳定性/听感测试，所以该值是基于既有证据的静态修正，不宣称已经通过真人音量验收。

## 启动介质审计

- `/boot` 为 40 MB vfat，使用约 14 MB，剩余约 27 MB；rootfs 剩余约 14 GB。
- factory bit SHA `16cb36f7...2a61`，v23 SHA `f12da25e...49b7`。
- `uEnv.txt` SHA `e211c7f8...53c2`，`boot.scr` SHA `7702e40c...3f8`。
- 现有启动入口为 `/etc/rc5.d/S99world-voice`；本轮不改该链接。
- FAT 仍有既有“未正常卸载”警告，正式写入必须逐件回读 SHA、`sync`，且不得覆盖原文件。

## 检查

- Python 编译通过；host unittest 共20项：18通过、2项因Windows无POSIX `sh`按设计跳过。
- 板端 BusyBox `sh -n`：autostart/init/control/fault-test 四个脚本全部通过。
- 板端无声故障注入：
  1. 坏 manifest -> exit 1、`DISABLE=BOOT_ASSET_HASH`、state=`FALLBACK_FACTORY_BOOT_ASSET_HASH`、factory `start` 被调用；
  2. 预置 `DISABLE=MANUAL` -> init 直接启动 factory，不创建 candidate PID。
- 板测输出：`BOARD_BOOT_FAULT_TEST_PASS cases=2 audio_started=0 fpga_changed=0`。
- 故障注入后原厂服务和双 PCM 仍 RUNNING，FPGA operating，taint 0。

## 下一步

独立提交后进入 Round28 持久安装：上传 rootfs 与 FAT 资产、逐件回读 SHA、原 init 原子备份、安装但暂不启动。由于最终启用会自动播放/采录，仍须在实际 `enable`/重启前取得当次操作者准备确认；用户已免除稳定性和提示音可闻验收，但未免除现场操作准备门。
