# PL-20261027-01：板端 CPU 基线等价回归

2026-10-27，基准提交 `45b167d`（实现提交 `50974e2`）。仅文件输入输出，不打开 ALSA、不录音、不播放。原 v23 服务在串口大包传输前停止，当前保持静默等待 PL 位流。

板卡 Cortex-A9 / Linux 5.15.0-xilinx，COM4。程序包 `world_exp_stage.tar.gz` 1,534,025 bytes，SHA256 `ead982263f03dae778144fdb8bb3a013c052a181e62ad483f79a02cf5c485fc8`，全部逐件 SHA 校验。输入为受控标准录音1前5秒的16k PCM16，与首轮电脑回归相同；源SHA及预处理见 `world_exp_round1_20261027.json`。

| 路径 | 分析RTF | 渲染RTF（含输出等待） | 削顶 | 结论 |
| --- | --- | --- | --- | --- |
| 原 v23 | 0.552449 | 0.330161 | 0 | 参考 |
| 新程序 CPU | 0.548558 | 0.326640 | 0 | 80000样本逐字节一致 |
| 新程序整数模型 | 0.553817 | 0.359643 | 0 | 相对CPU SNR79.0566dB，最大误差3 |

整数模型1227次调用、零fallback；其ARM软件运行成本不代表PL速度。当前分析仍是PS瓶颈，单纯卸载合成不能把总延迟按合成提速比例直接缩短。这里只验证新集成没有改变v23 CPU算法和定点误差可控，**尚无PL加速、真人音质、端到端延迟或长期稳定性通过结论**。

恢复位流已仅在`/tmp`生成、校验，未加载：原`/boot/bit/zynq7020.bit` SHA256 `16cb36f7161935896615ad12b000597088a6a9745856611162f1c44a51f82a61`；Linux字序恢复载荷4,045,564 bytes，SHA256 `af275946c15ae958e9bed16c12f6cab45b63ebecc18645cec24176315db7fc60`。不写启动分区。

复现：上传首轮所列构建文件与`board/world_exp_file_trial.py`至新`/tmp/codex_*`目录，按`deploy_manifest.json`校验后：

```sh
python3 world_exp_switch.py --base /tmp/codex_world_exp_20261027 --prepare
python3 world_exp_file_trial.py --base /tmp/codex_world_exp_20261027 --cpu-only
```

原始机器可读结果：`report/world_exp_cpu_board_20261027.json`。下一步：整机P&R与MCP复核，通过后静默加载候选，跑硬件向量和同输入PL文件回归；现场录放另行当轮确认。
