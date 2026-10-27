# PS-20261025-20：冻结 v1 配对特征与动态诊断

- 日期/角色：2026-10-26，Remote-PS-C / Codex。
- 基准：`fdade89b7cbf2aa6e8d1546e957535aca8ec7ae8`；已核对 main `9c42263ea3aa12898ad451f3c00915e816f039c4` 及开放 PR #9/#11/#13，无本任务冲突。
- 结果：诊断完整运行 PASS；v1 音质仍 **REJECTED**。没有新模型、训练或新的五门评分。
- 代码：`build/diagnose_remote_ps_c_fargan_v1.py`；完整逐对/逐维原始数值见同名 JSON，运行记录见同名 TXT。

## 数据和特征复核

200 对 source/teacher 的 800 项文件大小与 SHA 全匹配，200 份训练缓存 target 与交付 teacher 特征的截断前缀逐元素完全相同。辅助语料 split 仍为 192 train / 8 validation；本轮没有读取 Fixed-Male 或目标 Track WAV。缓存清单 SHA 为 `d305aab590730054f873a2cda25e0e1afb05b887bb3f9104d95047a7b72461ca`，与冻结检查点记录的原始清单 SHA 相同。

用 v1 已交付的同一 host 分析器，对 source/teacher float PCM 按 round→clip→PCM16 重新提取 20D 特征，只比较共同帧；没有覆盖训练标签或改变尾帧规则。

| 200 对的逐句 MAE 均值 | source | teacher |
| --- | ---: | ---: |
| 全部 20 维 | 0.0007785375 | 0.0005537752 |
| 倒谱维度 0–17 | 1.386792e-7 | 1.924352e-7 |
| 音高编码维度 18 | 0.0091938337 | 0.0063230675 |
| 周期相关维度 19 | 0.0063744169 | 0.0047489708 |

全局最大绝对差分别为 **1.702459217 / 1.282008648**，不能用低平均误差掩盖局部极值。各句最大差全部位于维度 18 或 19（source：188/12 句；teacher：159/41 句）。绝对差 >0.01 的元素比例逐句均值分别为 0.684880% / 0.584542%；0.01 只是诊断展示尺度，不是新增验收门。逐句最大差的帧号/维度已保存。

当前官方源码 `dnn/freq.h` 定义 NB_BANDS=18；`dnn/lpcnet_enc.c` 的 DCT 结果位于前 18 维，索引 18 是 dnn_pitch，索引 19 是变换后的相关量。`dnn/fargan.c` 由索引 18 计算周期，因此不能将该维直接称作 Hz。源码及构建哈希已经由 v1 模型交付清单固定。当前 native 与历史特征生产器不是同一历史构建；本轮没有证明逐位一致，也没有证据将残差归因于某个具体版本变化。

## 时间对齐诊断

按 10ms 帧计算 PCM 均方能量，取自然对数、下限 1e-8；固定 source 中间区间，teacher 测试 −30…+30 帧，所有偏移使用相同 source 支持区间。正值表示 teacher 较晚。此搜索仅描述数据，不重排特征，不选择模型参数。

- 零偏移相关：均值 **0.862052121**、中位数 **0.884509342**。
- 最佳偏移绝对值：中位数 **0ms**、P90 **10ms**、最大 **20ms**。
- 相比零偏移的相关增益：均值 **0.004550708**、最大 **0.056802167**。

在该诊断范围内，没有发现能量轮廓支持的大幅整体错位；这不能排除句内音素错位、音节变化或局部对齐问题，也不能证明 CER 失败的原因。

## 冻结模型在辅助 validation 上的行为

只使用此前选择 v1 检查点的 8 对/4616 帧，未继续优化模型。按原推理路径执行 PCA/标准化/冻结 mapper/训练分位截断。以训练集 y_mean 的常数输出为基线，按训练 y_std 归一化，各帧等权；差分只在各句内计算。

| 指标 | v1 | 训练均值基线 |
| --- | ---: | ---: |
| 归一化 MAE | 0.452730745 | 0.806939065 |
| 归一化 MSE | 0.374716520 | 1.028239846 |

20 维 MSE 均优于该常数基线，因此没有出现整体退化为均值输出。但高阶倒谱和音高的帧间动态明显偏弱：

| 索引 | 预测/teacher 标准差 | 预测/teacher 一阶差分 RMS | 预测与 teacher 相关 |
| --- | ---: | ---: | ---: |
| 14 | 0.669666 | 0.265881 | 0.615891 |
| 15 | 0.725126 | 0.270115 | 0.600047 |
| 16 | 0.743165 | 0.329042 | 0.703606 |
| 17 | 0.616981 | 0.228091 | 0.542385 |
| 18 | 0.817111 | 0.263190 | 0.775638 |
| 19 | 0.940430 | 0.498516 | 0.907483 |

这支持进一步检查时间动态学习，但无法区分应保留的语音动态和 teacher 分析器抖动；不能直接推断更大的差分损失会改善音质或源泄漏。辅助 validation 已用于原检查点选择，本轮不是独立验收。

## 复现

本机已有 v1 资产及缓存时，从本任务检出根目录运行：

```powershell
$env:PYTHONUTF8 = '1'
& 'build/generated/remote_ps_c_env/Scripts/python.exe' 'build/diagnose_remote_ps_c_fargan_v1.py'
if ($LASTEXITCODE -ne 0) { throw '诊断失败' }
```

最终完整运行退出 0，耗时 **26.734 秒**，包括 SHA 核验、400 次 host 特征提取及 8 句 mapper 推理。Python/依赖版本同 `ps_20261025_20_environment_20261026.lock.txt`。生成 PCM/特征留在 `build/generated/remote_ps_c_diagnostic_v1/`，未进入 Git。

另一台电脑需先按 `ps_20261025_20_github_model_receipt_20261026.md` 下载/校验/解压已发布 v1 完整包并准备锁定 Python 环境，按 `ps_20261025_20_paired_corpus_delivery_20261026.md` 取得已校验的配对语料。以下从检出根目录设置工作路径；两项接收路径替换为该电脑真实的非系统盘路径：

```powershell
$bundleRoot = 'E:\FPGA_workspace\receive-check\model\bundle'
$corpusRoot = 'E:\FPGA_workspace\receive-check\corpus\paired_hubert_fargan_corpus_v1'
$generatedRoot = Join-Path (Get-Location) 'build\generated'
$assetRoot = Join-Path $generatedRoot 'remote_ps_c_assets'
$modelRoot = Join-Path $generatedRoot 'remote_ps_c_hubert_fargan_v1'
$nativeRoot = Join-Path $generatedRoot 'remote_ps_c_native'
@($assetRoot, $modelRoot, $nativeRoot, (Join-Path $assetRoot 'paired_corpus_v1')) | ForEach-Object {
    New-Item -ItemType Directory -Path $_ -Force | Out-Null
}
Copy-Item -LiteralPath (Join-Path $bundleRoot 'hubert_base') -Destination $assetRoot -Recurse
Copy-Item -LiteralPath $corpusRoot -Destination (Join-Path $assetRoot 'paired_corpus_v1') -Recurse
Copy-Item -LiteralPath (Join-Path $bundleRoot 'mapper.pt') -Destination $modelRoot
Copy-Item -LiteralPath (Join-Path $bundleRoot 'statistics.npz') -Destination $modelRoot
Copy-Item -LiteralPath (Join-Path $bundleRoot 'native\fargan_probe_host.exe') -Destination $nativeRoot
$python = Join-Path $generatedRoot 'remote_ps_c_env\Scripts\python.exe'
$env:PYTHONUTF8 = '1'
& $python 'build/remote_ps_c_hubert_fargan.py' cache
if ($LASTEXITCODE -ne 0) { throw '缓存生成失败' }
& $python 'build/diagnose_remote_ps_c_fargan_v1.py'
if ($LASTEXITCODE -ne 0) { throw '诊断失败' }
```

此准备块用于新的空资产目录，沿用已经准备好的锁定环境。缓存重建只读取已批准的辅助语料，不需要重新训练；新清单的运行时间会改变 SHA，脚本同时记录当前缓存清单和检查点的历史清单 SHA，不把二者冒称相同。CPU/运行库变化可能改变浮点结果。本轮测试的是本机已有缓存；上述另一台电脑重建流程未在第二台实体电脑执行。

最初受限运行在 native 启动前返回 WinError 623，后续按已授权的正常 host 执行环境运行；诊断脚本首次 mapper 调用又因 Double/Float 类型不匹配退出。已将输入转为 float32，与原 infer 一致。两次失败原始记录和最终成功记录保存在 TXT 中；没有遗漏失败并声称首测通过。

## 结论与下一责任方

下一轮仍由 Remote-PS-C 在 `PS-20261025-20` 内处理。可将时间差分损失权重从 0.25 改为 1.0 作为一个预先声明的单变量假设；其余数据/模型/训练规则不动，只按辅助 validation 选择检查点，再对 Fixed-Male4 做一次原五门筛选。该实验尚未启动，不保证改善，尤其不能把 teacher 音高抖动当作必须恢复的细节。本轮没有修改任何权重或统计、分配规则、评价阈值，也未读取 Male5/Track9。

v1 原五门仍为身份 0.778814512 / P10 0.751711670 / 源泄漏 0.252929151 / UTMOS 2.418009599 / CER 0.235294118，源泄漏与 CER 未过。本轮不重新播放或评分，不进入 WAIT_LOCAL_TEST，不交 Hardware-A/B 试听或板测。没有录音、播放、真人试听、板卡、Cortex-A9、Vivado、RTL、PL 或实时验收。
