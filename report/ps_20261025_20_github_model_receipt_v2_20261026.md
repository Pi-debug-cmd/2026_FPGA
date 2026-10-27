# PS-20261025-20：v2 完整模型 GitHub 发布与干净下载复验

2026-10-26，Remote-PS-C。交付 **VERIFIED_GITHUB_DOWNLOAD_AND_INFERENCE**，质量仍 **REJECTED**。用户已明确授权“授权在当前公开仓库发布完整模型包”，本轮沿用该授权；没有改变仓库可见性、任务分配或约束文件。v1 原标签和模型包保持不变。

## 唯一版本与全部资产

- Release：https://github.com/Pi-debug-cmd/2026_FPGA/releases/tag/model-PS-20261025-20-hubert-fargan-v2；已发布 prerelease，draft=false。
- 标签 `model-PS-20261025-20-hubert-fargan-v2`，已核对指向源码提交 `0a8ae4e261cc098cc8c489a12865d9c28452fe64`。
- 附件 `PS-20261025-20_hubert_fargan_v2_windows_cpu.zip`，**198735391 bytes**；asset ID **678641359**。
- SHA-256 **`a669cb614dc4f71090b898da48e7fc127fbf016892dc3d655be1a535042a4441`**；GitHub server digest、重新下载后的字节数和 SHA 全部匹配。
- 解包后 **466** 项清单内文件的大小/SHA 全部校验（不含清单自身）；逐文件清单见 `model_delivery_PS-20261025-20_hubert_fargan_v2_20261026.json` 的 bundle_manifest 和 ZIP 内 bundle_manifest.json。

包含 v2 mapper、train-only统计、完整 HuBERT、嵌入 FARGAN 权重的 Windows host 程序、native源码/构建清单/许可、训练配置与历史、依赖锁和运行说明。不含 WAV、训练语料或缓存。其余来源和许可证沿用包内 provenance/notices，不作额外授权声明。

## 实测接收与运行

从 GitHub 附件端点下载到全新 `D:/fpga/receive-check/PS-20261025-20-hubert-fargan-v2/github-download/`；不是复制本地 ZIP。新建精确 detached checkout `download-code/` 和空 bundle 目录；Git对象共享自本地已推送仓库，工作树和模型为新建。独立 runtime 新建 venv 并复制已锁定依赖库，**没有测试重新 pip 安装**；Python 3.12.14/torch2.7.1+cpu，真实模块路径在 JSON。

在新检出内用以下等价入口运行（包装器增加 Python 文件打开审计和进程内存测量）：

```powershell
& ../runtime/Scripts/python.exe build/remote_ps_c_hubert_fargan_v2.py infer --assets bundle --output bundle --native bundle/native/fargan_probe_host.exe
```

退出 **0**。Python 文件打开审计没有发现访问原训练 generated 目录；模型和主要依赖从新接收目录读取，Python标准库仍来自既有基础运行时。PATH限制为 Windows 系统路径，清除 PYTHONPATH；缓存/临时文件均重定向至 D:/fpga 下的新目录。审计不等同于整个操作系统的文件追踪。此为同一电脑的隔离接收测试，**不是第二台实体电脑测试**。

推理含加载/合成 **2.750s**，本机 RTF **0.151098901**；包装器 **53.756680s**。Python 峰值工作集 **1110630400 bytes**、peak pagefile **2384629760 bytes**，不含 native 子进程。以上均不是 ARM/1GB DDR 可行性证据。

输出 **16kHz / mono / PCM16 / 291200 samples / 18.2s**，peak 0.488525391、RMS 0.070537007、clipping0。WAV SHA **`9e7f37895e8188b96909edad73b140fbcf5e7a14ebd3c1202605a27b339745e7`** 与本轮原五门评价 WAV 完全一致，故没有重新评分或选参。质量沿用身份0.778145609/P10 0.755978229/泄漏0.255133692/UTMOS2.574109713/CER0.235294118，泄漏与CER失败；不进入 WAIT_LOCAL_TEST，不交硬件或试听。

首次接收在上传成功后、下载前因未创建版本父目录而报 WinError3；补建父目录后继续核对同一个已发布附件，未覆盖资产。此失败与最终下载、校验、推理日志均保存在同名 TXT，不宣称首测成功。

完成后观察到 D 盘余量 378860003328 bytes（约352.84GiB）；C盘余量92154630144 bytes。新包、下载、隔离环境和输出均位于 D:/fpga；未记录本轮开始时C盘余量，因此不声称其占用完全不变。

## 另一台 Windows 电脑的完整接收命令

先选择空间充足的非系统盘。以下 D: 是示例，必须使用新的目标目录。需要 Git、已登录且可读取该仓库的 GitHub CLI，以及 Windows x64 Python3.12.14。依赖安装命令供重建；本轮实测环境使用复制锁定库，未验证全新 pip 安装。全部命令在同一 PowerShell 会话运行，不播放音频。

```powershell
$ErrorActionPreference = 'Stop'
$workspaceRoot = 'D:\PS-20261025-20-receive-v2'
if (Test-Path -LiteralPath $workspaceRoot) { throw 'Choose a new empty destination' }
New-Item -ItemType Directory -Path $workspaceRoot | Out-Null
Set-Location -LiteralPath $workspaceRoot
@('cache','tmp','downloads') | ForEach-Object { New-Item -ItemType Directory -Path $_ | Out-Null }
$env:TEMP = Join-Path $workspaceRoot 'tmp'
$env:TMP = $env:TEMP
$env:PYTHONUTF8 = '1'
$env:PIP_CACHE_DIR = Join-Path $workspaceRoot 'cache\pip'
$env:HF_HOME = Join-Path $workspaceRoot 'cache\hf'
$env:TORCH_HOME = Join-Path $workspaceRoot 'cache\torch'
$env:XDG_CACHE_HOME = Join-Path $workspaceRoot 'cache\xdg'
$env:UV_CACHE_DIR = Join-Path $workspaceRoot 'cache\uv'
git clone https://github.com/Pi-debug-cmd/2026_FPGA.git code
if ($LASTEXITCODE -ne 0) { throw 'Clone failed' }
git -C code checkout --detach 0a8ae4e261cc098cc8c489a12865d9c28452fe64
if ($LASTEXITCODE -ne 0) { throw 'Checkout failed' }
gh release download model-PS-20261025-20-hubert-fargan-v2 -R Pi-debug-cmd/2026_FPGA -p PS-20261025-20_hubert_fargan_v2_windows_cpu.zip -D downloads
if ($LASTEXITCODE -ne 0) { throw 'Download failed' }
$archive = Join-Path $workspaceRoot 'downloads\PS-20261025-20_hubert_fargan_v2_windows_cpu.zip'
if ((Get-Item -LiteralPath $archive).Length -ne 198735391) { throw 'ZIP size mismatch' }
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'a669cb614dc4f71090b898da48e7fc127fbf016892dc3d655be1a535042a4441') { throw 'ZIP SHA mismatch' }
Expand-Archive -LiteralPath $archive -DestinationPath code\bundle
$manifest = Get-Content -Raw -LiteralPath code\bundle\bundle_manifest.json | ConvertFrom-Json
if ($manifest.source_commit -ne '0a8ae4e261cc098cc8c489a12865d9c28452fe64' -or $manifest.files.Count -ne 466) { throw 'Manifest mismatch' }
foreach ($item in $manifest.files) {
    $file = Join-Path 'code\bundle' $item.path
    if ((Get-Item -LiteralPath $file).Length -ne $item.bytes -or (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256) { throw "File mismatch: $($item.path)" }
}
py -3.12 -m venv runtime
if ($LASTEXITCODE -ne 0) { throw 'Runtime creation failed' }
& .\runtime\Scripts\python.exe -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.7.1+cpu torchaudio==2.7.1+cpu
if ($LASTEXITCODE -ne 0) { throw 'CPU torch installation failed' }
& .\runtime\Scripts\python.exe -m pip install -r code\bundle\environment.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Locked dependencies installation failed' }
Set-Location code
& ..\runtime\Scripts\python.exe build/remote_ps_c_hubert_fargan_v2.py infer --assets bundle --output bundle --native bundle/native/fargan_probe_host.exe
if ($LASTEXITCODE -ne 0) { throw 'Inference failed' }
Get-Content -Raw bundle\inference.json
Get-FileHash -LiteralPath bundle\fixed_male4.wav -Algorithm SHA256
```

正常输出格式与 SHA 见上文。不同 CPU/运行库可能改变浮点结果；若出现差异应记录原始结果，不能宣称本轮位一致或重新调参后冒充同一模型。源输入只解码录音4；Male5/Track9继续锁定。非因果整句模型的部署边界、数据切分、训练/评价命令和全部指标见 `ps_20261025_20_hubert_fargan_v2_20261026.md/JSON/TXT`。

下一责任方 Remote-PS-C 保留失败实验与完整可下载资产；Hardware-A/B 暂不启动任何现场步骤。无录音、播放、真人试听、板卡、Cortex-A9、Vivado、RTL、PL或实时验收。
