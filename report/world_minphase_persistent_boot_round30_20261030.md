# PL-20261027-01 Round30：PL 持久部署与开机自动运行验收

## 结论

**ACCEPTED（按用户本轮免测边界完成持久部署）。** `music-button` 开机竞态已修复，wrapper 的旧状态误判也已消除。一次正常重启后，板卡自动选择 WORLD minphase PL candidate，状态为 `READY_CANDIDATE`，`DISABLE` 不存在，PL 驱动调用数从 2,278 继续增长至 13,751，采集与播放 PCM 均为 RUNNING。板卡最终保持 PL candidate 运行，没有恢复 v23。

本结论只覆盖部署、自动启动、PL 后端实际调用和基础运行态，不包含用户已明确跳过的提示音可闻性与长时间稳定性，也不把“融合最小相位阶段在 PL”表述为完整 WORLD 全部进入 PL。

## 修复与安装

- wrapper 与 autostart 在 candidate 启动前停止 `music-button`，只终止 `comm=aplay` 且 cmdline 精确包含 `/opt/hardware_test/test.wav` 的遗留进程，并最多等待 5 秒直到 PCM 关闭；没有全局 `killall aplay`。
- autostart 的 runtime 失败恢复路径也先静默开机测试音频，避免 busy PCM 阻断回退。
- 新 release 为 `/opt/world_voice_pl/releases/20261030_round30`，`current` 原子切换到该目录。
- wrapper 启动 daemon 前同时删除 PID 文件和旧 state，避免新的进程尚未写状态时读取上一轮 `FALLBACK_*` 或 `READY_CANDIDATE`。
- state 修复采用临时文件加 `mv` 原子替换；安装时不重启音频，板端回读 wrapper SHA-256 为 `4f70ab031bff21c685ef9fbcc51ef5484cb8878d6d7920dbbccad850f3789489`。

## 正常重启验收

- boot selection：`WORLD minphase PL candidate`
- service：PID 766，`READY_CANDIDATE`
- release：`20261030_round30`
- guard：`DISABLE` 缺失
- PL stats（首次复核）：`calls=2278, copy_in_ns=5040882, device_ns=882226167, copy_out_ns=39869490`
- PL stats（完整性复核）：`calls=13751, copy_in_ns=27846258, device_ns=5343948115, copy_out_ns=244609750`
- ALSA：`card0/pcm0p` 与 `card0/pcm1c` 均 RUNNING；owner 分别为 candidate 链路的 `aplay` 与 `arecord`
- 进程表中没有 `/opt/hardware_test/test.wav`，当前链路为 supervisor、`world_budget_v24`、arecord 和 aplay
- kernel taint 为 4096，来源是预期的 out-of-tree `world_minphase_dma` 模块

## 原文件完整性

重启后再次回读，原厂文件未被覆盖：

- factory bit：`16cb36f7...1f82a61`
- `uEnv.txt`：`e211c7f8...31c53c2`
- `boot.scr`：`7702e40c...a6383f8`
- factory v23：`f12da25e...18349b7`
- candidate gzip：`6a7fec99...b628d98`

## 检查与已知限制

- 本轮直接相关回归：21 项，19 通过、2 项因 Windows 无 POSIX `sh`按设计跳过；板端 BusyBox `sh -n` 与两个安装器均通过。
- 一次全 `sim` discovery 共 70 项，其中 66 通过、2 跳过、2 个无关 `target_profile_v2` 用例因仓库未提供被忽略的 `build/generated/world_register_20261016/target_t5_8_20s.profile.txt` 报错；本轮未伪造该外部生成资产。
- 重启停止旧 candidate 时，内核打印 Xilinx audio formatter 的 `Bad of_node_put()` 和 prepared-clock 警告；随后正常完成重启并自动进入新 candidate。用户已免除稳定性测试，因此本轮记录但未扩展为长稳修复。
- FAT 仍打印历史已有的“未正确卸载”警告；候选与原厂关键文件重启后哈希均匹配。
- 当前 supervisor 每 600 秒完成一轮后重新启动下一轮；本轮只验证开机后的首轮，不声称 10/30 分钟稳定性通过。

## 原始证据 SHA-256

- active：`26efb302c7fff1a7123ee7d6b14f322a23c3d5e4505e18a2092c593b64e14a24`
- state-fix install：`2e8d9a82a0e09628fbb18b2cc26ab28d5abfd91664b78234bf7b0236413c9613`
- reboot：`e47a61630b5cd4c0c716620ebc10d0d01934314efb0a9d190fc746aa3d3600cf`
- boot login：`4ef679a5e31ef15b5d54f6a0ebbe33383b18e037befad986b51e19aab82c6463`
- boot verify：`1fb32fe6bd2abeed9442005961eb2a481a316a67e3e8701bee2078bfb18eb3a6`
- integrity：`5acd27af43bb7d9b783bfc19783e60bbd398803aa5fa2fe93d442894e4569f78`

最终板卡状态：PL candidate active、双 PCM RUNNING、`DISABLE` absent；不恢复 v23。
