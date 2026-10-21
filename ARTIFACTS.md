# 本地大文件与生成物

GitHub 仓库保存本项目的源码、约束、脚本、文档、测试代码和关键配置。以下内容仍保留在本机，但不纳入 Git：

- Vivado/PYNQ 的缓存、综合实现输出、位流和临时日志；
- 可重新下载的神经网络权重、LLVC/RVC/FARGAN 等第三方参考仓库和工具可执行文件；
- 板卡系统镜像、编译产物以及历史预算构建目录；
- 除团队已批准并纳入 `人物音频资料/` 的 10 段 WAV 外，新的真人录音和测试生成音频。

这样可以避免仓库膨胀。`人物音频资料/` 已包含团队主动上传的真人录音；新录音仍按 `AGENTS.md` 的授权和清单规则处理。

## 模型交付与另一台电脑获取

具体到 Claude 的必读资料、上传内容、干净目录自测和板卡方接收门槛，见 [远端模型交付与接收](交接/远端模型交付与接收.md)。

**克隆或阅读 Git 仓库本身不会得到模型权重。** `.gitignore` 排除了 `*.pt`、`*.pth`、`*.ckpt`、`*.onnx`、`*.bin` 和 `build/generated/`。仓库里有训练/推理代码或评测报告，并不等于可运行模型已经交付。

Claude 或其他远端写作者把候选交给另一台电脑复现或板端验证时，应把可运行的模型资产打包成版本化归档，作为**本私有仓库的 GitHub Release 附件**发布；仓库中的正式报告记录 Release 标签、附件名称与下载位置。归档至少包含实际推理所需权重、配置、词表/码本或其他必要文件，以及运行说明。第三方可重新下载的大模型可单列来源、确切版本、文件 SHA-256 和获取步骤；如果缺少该依赖就无法推理，候选不得标为已交付。

每个候选的 `report/` 报告和 `coummucation.md` 记录至少包含：源提交 SHA、任务编号、模型用途（电脑音质上限/因果部署候选/板端实测）、Release 标签、每个附件的文件名/字节数/SHA-256、完整依赖和获取命令、预处理与输入输出格式、推理命令、复现指标、模型大小/算量/峰值内存/速度，以及尚未通过的门槛。只有可由另一台有仓库权限的电脑实际下载、校验并运行的候选，才能写“模型已交付”。电脑端音质上限不能因此宣称能部署到 Zynq-7020；板端能力仍按 `plan.md` 完成 Cortex-A9、PL、实时和真人试听验证。

例如，报告列出 Release 标签和附件名后，在具有该私有仓库读取权限且已登录 GitHub CLI 的电脑执行（先把前三行改为本机实际值，`E:` 仅是非系统盘示例）：

```powershell
$releaseTag = '填入报告中的标签'
$assetName = '填入报告中的附件名'
$workspaceRoot = 'E:\2026_FPGA_workspace'
$modelDir = Join-Path (Join-Path $workspaceRoot 'models') $releaseTag
New-Item -ItemType Directory -Force -Path $modelDir | Out-Null
gh release download $releaseTag -R Pi-debug-cmd/2026_FPGA -p $assetName -D $modelDir
Get-FileHash -Algorithm SHA256 (Join-Path $modelDir $assetName)
```

把输出与报告中的 SHA-256 逐字比对，再按该轮运行说明解压并推理。没有 Release 附件、下载权限或校验值时，必须记录缺口并标为 `BLOCKED`；不能把本地某台电脑独有的路径当成跨电脑交付。若单个附件超出 GitHub Release 限制，先拆分并提供有序重组与逐件校验说明，或在 `coummucation.md` 记录团队确认的替代存储位置及同等校验流程。
