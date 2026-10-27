# PS-20261025-20: public model release and clean GitHub download receipt

2026-10-26 · Remote-PS-C. **Delivery: VERIFIED_GITHUB_DOWNLOAD_AND_INFERENCE. Quality: REJECTED.**

The user explicitly authorized this exception on 2026-10-26: “授权在当前公开仓库发布完整模型包”. Repository metadata confirms public visibility. This authorizes this package publication in the current public repository; it does not rewrite AGENTS.md, ARTIFACTS.md, allocation, GitHub rules or repository visibility. The earlier private-delivery blocker and local tests remain historical evidence in `ps_20261025_20_model_archive_local_smoke_20261026.md` and `previous_local_archive_test` in the delivery JSON. That delivery blocker is resolved by this authorization and the successful online test below.

## Published assets

- Release: https://github.com/Pi-debug-cmd/2026_FPGA/releases/tag/model-PS-20261025-20-hubert-fargan-v1
- Tag: `model-PS-20261025-20-hubert-fargan-v1`; published prerelease, draft=false; verified target `94d2aa2237d9053d76616f22bc166ac1b7f92437`.
- Attachment: `PS-20261025-20_hubert_fargan_v1_windows_cpu.zip`; **198734997 bytes**.
- SHA-256: **`9532fe32d5ab707a51662b224f82a95abba901d9fc4fcc4276cedd0cf2ca4e6a`**. GitHub server digest, downloaded bytes and downloaded SHA-256 all match.
- Asset URL: https://github.com/Pi-debug-cmd/2026_FPGA/releases/download/model-PS-20261025-20-hubert-fargan-v1/PS-20261025-20_hubert_fargan_v1_windows_cpu.zip; asset ID 678438781.
- All **466** manifest-listed internal files verified before inference. Full per-file sizes/hashes remain in `model_delivery_PS-20261025-20_hubert_fargan_v1_20261026.json` and the package manifest.

The complete package includes mapper/statistics, HuBERT, native FARGAN executable with embedded weights, source/provenance/notices, training configuration, dependency lock and README. It contains no WAV, training corpus or hidden cache. Third-party terms are retained in the package.

## Clean reception and execution

The ZIP was downloaded from the authenticated GitHub asset endpoint into the newly created empty `D:/fpga/receive-check/PS-20261025-20-hubert-fargan-v1/github-download` directory. It was not copied from the local package. A fresh detached shared Git clone at the exact already-pushed source commit was made in `download-code`; only Git objects are shared, and the working tree/model directory were fresh. This is an isolated same-computer receive test, not a second physical computer test.

The independent runtime is Windows x64 Python 3.12.14 / torch 2.7.1+cpu. Locked dependency libraries were copied into a separate venv; fresh pip installation was not tested. Runtime module paths are captured in the JSON. The file-open audit guard rejected the original training/generated tree; no prohibited access was attempted. Model loading is offline, and the CLI directs its caches/temp files to the new checkout's `build/generated/remote_ps_c_cache`. PATH was limited to Windows system paths. All large files remain under D:/fpga (D: free space observed before the receive test: about 356.53 GiB).

Measured entry point from `download-code`:

```powershell
& ../runtime/Scripts/python.exe build/remote_ps_c_hubert_fargan.py infer --assets bundle --output bundle --native bundle/native/fargan_probe_host.exe
```

Exit **0**; wrapper wall time **8.387427 seconds**; reported full model load/inference/synthesis **2.734 seconds**, desktop RTF **0.150219780**. Output is mono PCM16 / 16 kHz / 291200 samples (18.2 seconds), peak 0.540161133, RMS 0.070893222, clipping fraction 0.

Output SHA-256 **`ee548f1aef80fc9a032e3557b08090091d1bb91f05a512b20b1b654ed56af109`** exactly matches the original strict evaluation WAV. The metrics were therefore reused without a new metric run. Python peak working set **1111740416 bytes**, peak pagefile usage **2381811712 bytes**; native child excluded. Raw terminal evidence is `ps_20261025_20_github_model_smoke_20261026.txt`; structured runtime, formats, asset and inference evidence are in `ps_20261025_20_github_model_receipt_20261026.json`.

## Commands for another Windows computer

First choose a non-system disk with enough free space; D: below is an example. Run from a new destination, with Git, GitHub CLI and Windows x64 Python 3.12.14 available. The commands stop on nonzero native exit codes. They never play audio.

```powershell
$ErrorActionPreference = 'Stop'
$workspaceRoot = 'D:\PS-20261025-20-receive-v1'
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
if ($LASTEXITCODE -ne 0) { throw 'Git clone failed' }
git -C code checkout --detach 94d2aa2237d9053d76616f22bc166ac1b7f92437
if ($LASTEXITCODE -ne 0) { throw 'Exact checkout failed' }
gh release download model-PS-20261025-20-hubert-fargan-v1 -R Pi-debug-cmd/2026_FPGA -p PS-20261025-20_hubert_fargan_v1_windows_cpu.zip -D downloads
if ($LASTEXITCODE -ne 0) { throw 'Release download failed' }
$archive = Join-Path $workspaceRoot 'downloads\PS-20261025-20_hubert_fargan_v1_windows_cpu.zip'
if ((Get-Item -LiteralPath $archive).Length -ne 198734997) { throw 'Archive size mismatch' }
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne '9532fe32d5ab707a51662b224f82a95abba901d9fc4fcc4276cedd0cf2ca4e6a') { throw 'Archive SHA mismatch' }
Expand-Archive -LiteralPath $archive -DestinationPath code\bundle
$manifest = Get-Content -Raw -LiteralPath code\bundle\bundle_manifest.json | ConvertFrom-Json
if ($manifest.source_commit -ne '94d2aa2237d9053d76616f22bc166ac1b7f92437' -or $manifest.files.Count -ne 466) { throw 'Manifest mismatch' }
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
& ..\runtime\Scripts\python.exe build/remote_ps_c_hubert_fargan.py infer --assets bundle --output bundle --native bundle/native/fargan_probe_host.exe
if ($LASTEXITCODE -ne 0) { throw 'Inference failed' }
Get-Content bundle\inference.json
Get-FileHash bundle\fixed_male4.wav -Algorithm SHA256
```

The installation commands are the packaged reconstruction instructions; this receive test used copied locked libraries as stated above. Float results can vary with CPU/runtime. Expected tested output hash is given above; different output requires the same strict quality protocol before claiming equivalence. The input is the approved repository recording 4; no local training data is required. Preprocessing averages channels, resamples to 16 kHz with polyphase resampling and preserves physical timestamps; train-only statistics and frozen checkpoint are loaded from the bundle.

## Quality and next responsibility

Original five-gate results: identity **0.778814512**, P10 **0.751711670**, strict source leakage **0.252929151** (requires ≤0.10, FAIL), UTMOS **2.418009599**, CER **0.235294118** (16/68; requires ≤0.15, FAIL). Delivery verification does not pass these failed quality gates. No WAIT_LOCAL_TEST, listening or board handoff is permitted. Fixed-Male 5 and target Track 9 remain locked. The full-utterance HuBERT/BiGRU candidate is noncausal; desktop memory/RTF do not establish Cortex-A9, 1 GB DDR, latency or real-time feasibility.

Next responsibility remains Remote-PS-C: preserve this failed candidate as reproducible evidence and assess any subsequent software-only round within PS-20261025-20. Hardware-A/B should not initiate listening/board work for v1. No playback, recording, human listening, board, Cortex-A9, Vivado, RTL, PL or realtime acceptance occurred.
