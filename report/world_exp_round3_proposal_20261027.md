# PL-20261027-01：Round 3 相位打包及现场回归入口

基准 `ffe7189`。本轮保持RTL位流和v23语音算法不变，PS相位归一从通用remainder改为有界整数圈数乘减；超出安全范围整帧CPU fallback并计数，不能伪称全PL。CPU/整数模型host5秒男声1回归SNR79.0566dB、最大PCM16误差3不变，ARM/host已编译。下一步同输入板测，再决定是否请求现场。

现场监督入口只做必要扩展：可指定独立临时base和ALSA period/buffer/start-delay；默认值与v23原脚本一致。解析日志按kind选runtime，避免把新增PL后端统计误当runtime；请求WORLD_EXP=pl时必须mode2、calls>0且零fallback。只终止自身子进程，保存和恢复mixer。

准备中的短现场配置为20秒，prefill100ms、period256、采集buffer2048、播放buffer1024、start-delay16000µs、原增益。它是延迟/连续性探索配置，不是p95≤100ms实测证据。必须先获得当轮操作者准备确认后才能执行--run；未播放、未录音。
