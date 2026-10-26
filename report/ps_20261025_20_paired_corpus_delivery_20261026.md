# PS-20261025-20 HuBERT→FARGAN 配对语料交付

## 结论

Remote-PS-C PR #11 所缺的同内容配对语料已从 Hardware-A 受控资产生成便携包。该包包含 200 对样本（192 train / 8 validation）、每对的 source/teacher 16 kHz float32 PCM 和 source/teacher 20 维 FARGAN 特征。包内路径均为相对路径，且附逐文件 SHA-256 校验器。

本记录只解除“配对语料不可跨电脑取得”的阻塞，不代表训练、客观门、真人试听、Cortex-A9、PL 或实时性通过。Track 9 未进入本包；teacher 来自项目已有 CosyVoice3 配对资产，尚未获得真人质量验收。

## Release 资产

- 私有仓库：`Pi-debug-cmd/2026_FPGA`
- Release 标签：`asset-PS-20261025-20-paired-corpus-v1`
- Release URL：`https://github.com/Pi-debug-cmd/2026_FPGA/releases/tag/asset-PS-20261025-20-paired-corpus-v1`
- 附件：`PS-20261025-20_paired_hubert_fargan_corpus_v1.zip`
- 字节数：`125109914`
- SHA-256：`956dead3c76b1e214cc6baf5a1dca0b7e083eebb2771e417b722df6e2181366c`
- 归档内文件：803（800 个数据文件、manifest、README、校验器）
- Release 目标提交：`2888c7cb6abff1547aff451d082e8db686a6bc08`

## 生成与本机独立解包检查

```powershell
python tools/package_remote_ps_c_fargan_corpus.py `
  --asset-root 'C:\Users\World\Desktop\2026_FPGA' `
  --output 'C:\Users\World\Desktop\2026_FPGA\build\generated\remote_ps_c_delivery_20261026'
```

生成脚本同时核对原始 PCM manifest 的 SHA-256、特征文件存在性、float32 对齐和 20 维特征长度。将 ZIP 展开到新的 `receive_check_20261026_1540` 目录后执行随包校验器，结果为：

```text
PASS 200 800
```

## Remote-PS-C 获取与校验

先按 `交接/远端模型交付与接收.md` 选择空间足够的非系统盘项目总目录；以下 `E:` 只是示例，必须改为该电脑真实路径。

```powershell
$workspaceRoot = 'E:\2026_FPGA_workspace'
$receiveDir = Join-Path $workspaceRoot 'receive-check\PS-20261025-20-paired-v1'
New-Item -ItemType Directory -Force -Path $receiveDir | Out-Null
gh release download 'asset-PS-20261025-20-paired-corpus-v1' `
  -R Pi-debug-cmd/2026_FPGA `
  -p 'PS-20261025-20_paired_hubert_fargan_corpus_v1.zip' `
  -D $receiveDir
$zip = Join-Path $receiveDir 'PS-20261025-20_paired_hubert_fargan_corpus_v1.zip'
Get-FileHash -Algorithm SHA256 $zip
Expand-Archive -LiteralPath $zip -DestinationPath $receiveDir
python (Join-Path $receiveDir 'paired_hubert_fargan_corpus_v1\verify_bundle.py')
```

预期 SHA-256 与上文完全一致，最后一行输出 `PASS 200 800`。训练只读取 `portable_manifest.json` 中 `split=train` 的 192 行；8 行 `validation` 仅用于选择检查点，不得混入训练。

## Release 下载复验

2026-10-26 从上述私有 Release 下载附件到新的 `build/generated/release_receive_check_20261026_1550` 目录，未读取打包暂存目录。GitHub 返回附件状态 `uploaded`、大小 `125109914` bytes、digest `sha256:956dead3...1366c`；本地重新计算得到同一 SHA-256，展开后随包校验器输出 `PASS 200 800`。因此跨电脑附件已可下载且内容与发布前归档一致。

## 当前责任方

Release 下载复验通过后，Remote-PS-C 在 PR #11 分支继续 HuBERT→FARGAN 训练和离线客观评测。达到全部客观门后只能标为 `WAIT_LOCAL_TEST`，由 Hardware-A/B 另行进行现场与板端验收。
