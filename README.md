# 可注册目标声线实时变声器（2026 嵌赛 FPGA 赛道）

平台：野火 Zynq-7020（`xc7z020clg400-2`），Vivado 2018.3，优先本板适配的 PYNQ。目标：**只注册目标声线，任何未录入、未校准的陌生说话人对麦克风讲话，即可在板上实时转换并输出同一目标音色**；截止 2026-11-06。

当前阶段：**基础链已验证，目标音色未达标**。浮点/定点参考、17 项自动验证、变调 RTL 比对与独立综合、板端 PS 数值 12 组、PS-only 实时升调听辨、WORLD 实时 v22 现场、Seed-VC 参考离线审计均已完成；目标音色、多人泛化、板上现场注册闭环与定量延迟尚未通过。

## 先读这两个

- [项目查阅指引](project_guide.md)：**唯一入口**，含现行硬约束、当前技术判断、位置与可运行入口、板端事实。
- [总计划](plan.md)：截止日期、日历与 G1～G7 门槛、技术顺序、风险决策。

其余常用入口：接手清单见 [项目状态](team_project/project_status.md)，开发记录见 [协作记录](report/ai_worklog.md)，硬件事实见 [硬件核查](board/hardware_inventory.md)，现场测试见 [实时测试说明](board/world_live_trial.md)，队友历史成果见 [交接审阅](team_project/handoff_review.md)。

## 现行硬约束（2026-10-16 用户确认）

不接电脑、板上自足：**准备阶段（现场注册目标声源 + 板上构建音色转化模型）与实时转换阶段都在板上完成**；目标音色由演示现场录制的几句话当场建模；输入者免录入免校准；多个输入者转换到同一目标。详见 [需求记录](report/onboard_standalone_requirement_20261016.md)。

## 运行软件参考

从项目根目录执行，需要带 NumPy 的 Python 3.9+（系统 `python` 为 3.13.9；项目隔离依赖为 cp312，见 project_guide 入口表）。此参考用于电脑端算法实验，不代表板端速度。

```powershell
python -m unittest discover -s sim -v
python src/reference/pitch_shift.py data/input.wav data/output.wav --ratio 1.25 --block 256
./build/run_bypass_sim.ps1
./build/run_pitch_sim.ps1
python -m build.run_reference_demo
```

输入必须为单声道、未压缩 PCM16 WAV；采样率原样保持，`ratio=1` 为逐样本旁路，`0.5～2.0` 用于固定比例升降调。`data/input.wav` 由团队自备，不在仓库预置真人语音。参考采用双延迟读头、线性插值与三角交叉淡化；1024 样本窗口在 16kHz 对应 64ms 延迟扫描范围，不是设备到设备实测延迟。升调存在高频混叠风险，固定比例变调不等于目标声线拟合。

离线评测（身份/源泄漏/预测自然度/内容四项指标）：

```powershell
& 'C:/Users/World/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -u build/audit_seed_reference_20261016.py
```

## 目录约定

| 目录 | 用途 |
| --- | --- |
| `src/reference/`、`src/ps/`、`src/rtl/`、`src/kernel/` | 浮点/定点算法参考、ARM 侧、RTL 与内核模块 |
| `sim/` | 电脑端自动验证与 RTL 测试台 |
| `build/` | 仿真脚本、综合 Tcl、评测入口；生成物在 `build/generated/` |
| `board/` | 板卡信息、现场脚本与测试说明 |
| `report/` | 正式证据：JSON 报告、原始日志、开发记录与协作记录 |
| `team_project/` | 当前范围、状态、分工、接口与契约 |
| `data/` | 注册与对照音频、画像配置（非正式证据） |
| `交接/` | 队友历史总交接与核心材料；`交接/归档_md_20261016/` 为本次整理的归档 |
| `tmp/` | 临时产物，可清理 |

根目录只保留 `AGENTS.md`、`code_rule.md`、`README.md`、`project_guide.md`、`plan.md` 与最新的 `handoff_<日期>.md`；历史 md 一律进 `交接/归档_md_20261016/`。生成文件放 `build/generated/` 或 `tmp/`，正式证据放 `report/`，不往厂商资料盘写输出。

独立综合复现：

```powershell
New-Item -ItemType Directory -Force build/generated/axis_bypass_synth | Out-Null
& 'D:/USER_Software/Xilinx_Vivado/Vivado/2018.3/bin/vivado.bat' -mode batch -nojournal -log build/generated/axis_bypass_synth/vivado.log -source build/synth_bypass.tcl
```

综合阶段报告有时钟源/偏斜估计限制，也没有完整输入输出时序约束，不能当作整机实现时序通过。当前没有发布 bitstream。
