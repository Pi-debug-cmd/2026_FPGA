# PL-20261027-01 Round26：可闻提示音修正

## 结论

**PROPOSED / WAIT_LOCAL_TEST。** 针对 Round25 用户“我刚刚没有听到提示音”，监督器把短双音改为同一 playback stream 内的“静音预热 + 三段递增长音 + 尾部静音”，并新增 `--prompt-only`。该模式只配置播放 mixer、播放提示、恢复 mixer，明确不启动 arecord 或 WORLD；因此可以先由操作者单独确认提示可闻，再决定是否执行真人录入。

本轮仅完成代码和本机 mock 回归，没有播放、录音、加载板卡或改动 PL。

## 改动

- 新提示总长 97,920 帧（32 kHz，约 3.06 秒）：
  - 0.80 秒静音预热，让 WM8960/DAPM 在同一播放流中完成启动；
  - 660/880/1175 Hz 三段递增音，每段 0.55 秒；
  - 段间各 0.18 秒静音，末尾 0.25 秒静音；
  - 数字峰值从 0.12 提高到 0.30，每段保留 10 ms 左右淡入淡出。
- 正式录入前原有 2 秒准备窗口不变。
- `--prompt-only` 只依赖 ALSA/mixer 和 PCM idle；结果显式写入 `capture_started=false`、`world_started=false`，保存 mixer 前后状态并始终尝试恢复。
- 正常 `--check` 和 `--run` 的二进制 SHA、PCM idle 等前置检查不放宽。

## 检查

- `python -m py_compile board/live_world_trial.py sim/test_live_world_supervisor.py`：通过。
- `python -m unittest sim.test_live_world_supervisor -v`：17/17 通过。
- 新增回归验证：前 25,600 帧双声道全零、总帧数 97,920、实际峰值在 0.29..0.30、频率元数据 `[660,880,1175]`、2 秒准备延迟只调用一次。
- 新增 prompt-only 回归验证：`subprocess.Popen` 从未调用，mixer restore 恰好一次。
- 旧成功路径夹具补齐当前监督器早已要求的 `kind=world_raw_stream_runtime`；首次运行因忽略的夹具父目录不存在而 17 项在建临时目录前报错，创建该目录后暴露4个旧夹具字段缺失，修正后最终17/17通过。该过程不作为算法失败。
- `git diff --check`：通过。

源码 SHA：监督器 `63802aef6b0a1ebcdb3fb285a6893de54becd675e4dd9340354d8a23de7182ef`（20,369 bytes）；测试 `67b64b287223b9e74201c7d67a2ab236897c991d5ade4520785b824191a1394a`（9,566 bytes）。

## 验收边界与下一步

本机证明提示波形和控制流程正确，不证明耳机实际可闻。独立提交后，Hardware-A / Codex 必须重新询问操作者是否准备，只部署监督器并执行一次 `--prompt-only`；用户明确确认听到三段递增音后，才可认领下一次60秒录入。若仍不可闻，应定位 codec/模拟播放路径，不得继续真人录入。
