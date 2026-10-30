# PL-20261027-01 Round29：持久 PL 首次启用与重启结果

## 结论

**REJECTED（手动启用通过，开机自动启用被 `music-button` 竞态破坏）。** 首次删除 `INSTALL_GUARD` 后，candidate 成功加载并进入实时转换：状态 `READY_CANDIDATE`、`DISABLE` 不存在、module 已加载、PL calls 达到 2,145、双 PCM 均 RUNNING。正常重启后，candidate 也成功自动加载并报告 ready，但同为 `S99` 且字典序更早的 `music-button` 遗留了 `aplay /opt/hardware_test/test.wav`，占用 playback；WORLD preflight 因 `AUDIO_BUSY` 退出 1，保险逻辑写入 `DISABLE=RUNTIME_1`。

因此“手动启用可用”成立，但“开机自动进入 PL”尚未通过。按用户最新要求，本轮结束时没有主动恢复 v23：已停止错误回退服务并终止确认过的孤儿 aplay PID 894，板子保持静默、PCM closed；从启动日志与恢复断点推断 FPGA 仍为 candidate，module 已卸载，taint 4096。

## 首次手动启用

- preflight：`INSTALL_GUARD` 存在；factory bit/uEnv/boot.scr/v23/candidate gzip 哈希匹配，rootfs/boot manifests 全通过。
- `world-pl-control enable` 返回 0；状态 `READY_CANDIDATE`，`DISABLE` 缺失，FPGA operating，module live。
- 进入运行后驱动统计：`calls=2145, copy_in_ns=4410900, device_ns=830175412, copy_out_ns=35474790`；双 PCM RUNNING。
- autostart 日志包含 candidate load、module、preflight、三段提示及 `WORLD_LIVE_STARTED seconds=600`。

一次诊断命令中的 `ps | grep -E` 引号被串口调用层剥离，意外把 `world_budget_v24|arecord|aplay` 解析为额外管道命令；额外 `aplay` 因设备 busy、`arecord` 因参数不完整立即失败，未改变正在运行的 calls/PCM 状态。该操作失误保留在原始日志中。

## 重启失败根因

重启时 rc5 同时存在：

- `S99music-button -> ../init.d/music-button`
- `S99world-voice -> ../init.d/world-voice`

按字典序 `music-button` 先运行。其 stop 只终止 listener/evtest，不处理 listener 已启动后脱离的 aplay 子进程。实测 PID 894：`comm=aplay`、`exe=/usr/bin/aplay`、PPid 1、命令为 `aplay /opt/hardware_test/test.wav`，独占 pcm0p。

包装服务随后成功加载 candidate 并报告 ready，但 runtime 在 `audio_preflight()` 发现 pcm0p owner PID 894，抛出：

`AUDIO_BUSY: {"pcm0p": "state: RUNNING ... owner_pid: 894", "pcm1c": "closed"}`

autostart 正确将其标为 `AUTOSTART_FAILURE_RUNTIME_1` 并写 DISABLE。随后的 in-place restore 同样被 busy PCM 的断言挡住；factory start 不能等同于位流恢复成功。

## 最终静默状态

依照用户“现在不用恢复 v23”的要求，没有加载 factory restore。已停止 factory daemon、停止 music-button，并仅终止已确认的 PID 894。最终双 PCM closed、FPGA manager operating、`world_minphase_dma` absent、`DISABLE=RUNTIME_1`、state=`FALLBACK_FACTORY_RUNTIME_1`、taint 4096。

## 修复方向

Round30 必须在 wrapper 启动 candidate 前：

1. 停止 `music-button` listener；
2. 只终止 cmdline 精确包含 `/opt/hardware_test/test.wav` 的遗留 aplay，不做全局 `killall aplay`；
3. 等待 pcm0p/pcm1c 均 closed 后才启动 autostart；
4. 更新已安装 wrapper/manifest，删除 `RUNTIME_1` guard，重新启用并重启；
5. 最终保持 PL candidate，不主动恢复 v23。
