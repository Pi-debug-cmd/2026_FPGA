# PS-20261021-10：多轨权重收紧 Round 13

日期：2026-10-24

角色：Hardware-A / Codex（电脑端离线算法）

状态：**REJECTED**

Round 12 暴露后，本轮保持 Seed-VC、30 步、`CFG=1.10`、`seed=20261018`、总提示 10 秒、起点裁切和评估器不变，只把目标提示从 Track 5～7 各 2 秒 + Track 8 4 秒改为 Track 5～7 各 1 秒 + Track 8 7 秒。

结果为身份 `0.4916`、P10 `0.4523`、严格泄漏 `0.1382`、UTMOS `2.6273`、CER `0.0612`。相对 Round 12 原候选的身份 `0.5666`、泄漏 `0.1250`，目标身份下降且源泄漏进一步恶化，因此明确拒绝。“增加 Track 8 占比”在当前模型中并不能单调压低源残留。

提示 SHA-256 为 `828cfcfc0551bd516c324930f77c2bee13847269dd96a9fdbaed7007f02dbc7a`，输出 SHA-256 为 `22221760b7d08eb4e31d2b26be80ccfd0e7377950b391089d065ee6b68405f99`。输出未播放，生成 WAV 未提交；本轮没有触碰板卡，v23 保底不变。

复现命令：

```powershell
D:\Anaconda\envs\yolo\python.exe -S build\run_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --source build\generated\seed_fixed_male_20261024\round12_new_session_capture.wav --tag round13_mix10_round12 --target-mode multi3x1_track8x7 --source-onset-trim --cfg 1.10 --seed 20261018 --steps 30
D:\Anaconda\envs\yolo\python.exe -S build\evaluate_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --manifest build\generated\seed_fixed_male_20261024\round13_mix10_round12\manifest.json --output build\generated\seed_fixed_male_20261024\round13_mix10_round12\metrics.json
```
