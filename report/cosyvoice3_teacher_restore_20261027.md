# CosyVoice3教师环境恢复状态

PS-20261021-10，Hardware-A，2026-10-27，基准5a53f54。此项是训练前依赖恢复，不是完成的训练轮或推理测试。

- 独立根目录：D:/2026_FPGA_teacher_workspace；不修改原yolo环境或用户RTL/PL。
- 源码官方FunAudioLLM/CosyVoice，固定074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc；Matcha-TTS子模块固定dd9105b34bf2be2230f4aa1e4769fb586a3c824e；clone/fetch/submodule命令已退出0。
- 模型官方FunAudioLLM/Fun-CosyVoice3-0.5B-2512，固定29e01c4e8d000f4bcd70751be16fa94bf3d85a18，与历史公共教师一致。build/restore_cosyvoice3_assets_20261027.py下载metadata中14个必需文件，对LFS文件核验官方SHA-256及字节数，其他文件记录下载SHA-256及字节数；中断后.part支持HTTP Range续传。下载尚未完成，asset_manifest.complete不可视为true。
- 模型session38601仍在下载；至少配置/README及campplus已完成校验，speech_tokenizer_v3仍在传输。此处为启动快照，最新状态必须重新查询进程/manifest，不能只依赖本报告。
- venv以D:/Anaconda/envs/yolo/python.exe --system-site-packages创建，重用已有torch2.8.0+cu128；这不是可独立交付环境。torchaudio2.8.0+cu128已安装入venv，其他教师依赖仍由session5662安装。缓存/TEMP/TMP/HF_HOME/TORCH_HOME位于任务根内。
- 未加载教师、未生成源专用配对、未训练、未读取录音4/5或Track9音频、未播放、未板测。依赖安装和模型完成后仍须import/GPU/训练素材推理检查，不能宣称训练监督已齐全。

模型复现入口：Python3.12 build/restore_cosyvoice3_assets_20261027.py --workspace D:/2026_FPGA_teacher_workspace。源码为官方定点fetch及recursive submodule update，不能复制运行旧脚本的硬编码路径。

下一步核验两个活跃进程是否完成，再检查依赖与GPU、目标参考SHA及训练录音教师内容。不恢复无机制依据的参数扫描，原Round108上限不变。
