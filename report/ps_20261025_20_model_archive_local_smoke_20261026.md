# PS-20261025-20: corrected model archive and clean local smoke

2026-10-26 · Remote-PS-C. **Quality: REJECTED. Local package smoke: PASS. Cross-computer delivery: BLOCKED_PRIVATE_RELEASE.** This is a packaging/receive test round, with no new model selection or quality evaluation.

The portable relative-path fix is source commit **`94d2aa2237d9053d76616f22bc166ac1b7f92437`**, already pushed to task PR #11. It supersedes the first portable package bound to `74b16db`. The weights/statistics/native executable are unchanged. The original strict quality results remain identity 0.778814512, identity P10 0.751711670, leakage 0.252929151, UTMOS 2.418009599, CER 0.235294118. Leakage/CER fail; no WAIT_LOCAL_TEST or hardware handoff is allowed.

## Complete local archive

- Intended tag (not created): `model-PS-20261025-20-hubert-fargan-v1`, to target exactly the source commit above.
- Attachment: `PS-20261025-20_hubert_fargan_v1_windows_cpu.zip`.
- Bytes: **198734997**; SHA-256: **`9532fe32d5ab707a51662b224f82a95abba901d9fc4fcc4276cedd0cf2ca4e6a`**.
- Local path: `D:/fpga/.git-repair/build/generated/remote_ps_c_release_v1_fixed/PS-20261025-20_hubert_fargan_v1_windows_cpu.zip`.
- 466 manifest-listed files, 239453224 bytes before compression (excluding manifest itself). Full necessary-file names/sizes/SHA-256 and original model provenance are recorded in `model_delivery_PS-20261025-20_hubert_fargan_v1_20261026.json`.

The package includes mapper.pt, train-only statistics.npz, three HuBERT files, Windows CPU FARGAN executable with embedded official weights, exact build manifest, Opus audit sources/notices, HuBERT provenance manifest, training configuration/history, environment lock and README. It contains no source/target raw WAV, generated audio, teacher/training corpus or hidden model cache. All inference assets are present; raw input uses only the approved repository recording 4. Third-party terms remain applicable as described in the included notices/provenance.

## Clean local smoke evidence

A new detached shared Git clone at the exact pushed source SHA was created under `D:/fpga/receive-check/PS-20261025-20-hubert-fargan-v1/code-fixed`. The locally copied ZIP hash/size and all 466 internal files were verified before inference. The model directory was empty before extraction. Code objects are shared with the existing checkout, but the working tree is fresh. A separate newly created Python venv contains copies of locked installed dependency libraries. This verifies runtime isolation; **no fresh pip installation or online dependency retrieval is claimed**.

The invocation below ran from the clean code root, using the independent runtime executable one directory above:

```powershell
& ../runtime/Scripts/python.exe build/remote_ps_c_hubert_fargan.py infer --assets bundle --output bundle --native bundle/native/fargan_probe_host.exe
```

The measured test wraps that same entry point with a Python file-open audit guard rejecting access to the original `D:/fpga/.git-repair/build/generated` tree. No prohibited access was attempted. Imported NumPy/SciPy/SoundFile/Torch/Transformers paths are all in the independent runtime. PATH was reduced to Windows system paths, so no compiler-directory runtime DLLs were assumed. The input source comes from the new checkout; all weights/statistics/native code come from the unpacked package.

Exit code **0**. Full process wrapper wall time **7.7018374 seconds**; reported model-load/inference/synthesis time **2.563 seconds**, host RTF **0.140824176**. Output mono PCM16, 16 kHz, 291200 samples/18.2 seconds, peak 0.540161133, RMS 0.070893222, no clipping. Output SHA-256 **`ee548f1aef80fc9a032e3557b08090091d1bb91f05a512b20b1b654ed56af109`** exactly matches the original evaluation input. No metric rerun is needed for this identical WAV.

Windows GetProcessMemoryInfo reports Python peak working set **1111027712 bytes**, peak pagefile usage **2381021184 bytes**; the native child is excluded. These are desktop process measurements, including Python/libraries/full-utterance execution, not a board memory budget. The 1 GB Cortex-A9 deployment claim remains unproven; this noncausal full-utterance model is only an offline candidate. Original terminal output is retained in `ps_20261025_20_clean_smoke_20261026.txt`; structured runtime/module evidence is in the delivery JSON.

## Online delivery blocker

An authenticated repository metadata read returned **`private=false`**. `ARTIFACTS.md:18` requires the archive to be an attachment in “本私有仓库的 GitHub Release”; `交接/远端模型交付与接收.md:39` repeats the private Release requirement. The first publish script checked this condition before making any mutation and stopped. No Release/tag was created, no model was uploaded, and visibility/allocation/rules were not changed. The user has been asked to identify an authorized private destination or explicitly authorize publication of the full model in the current public repository.

Accordingly, there is **no published Release URL and no GitHub download receipt**. Local archive smoke success is not cross-computer model delivery. The metadata uses separate quality/delivery fields to avoid treating a passed packaging test as passed quality or completed delivery. After the destination is resolved, the remaining work is to publish this exact archive against the stated code SHA, download it into another empty model directory, verify its hash/internal manifest, repeat the same inference, and submit that receipt separately. Instructions and dependency versions are already included in the package; no guesswork or original training cache should be needed.

All generated data, runtime, package and cache remain under D:/fpga. Fixed-Male 5 and target Track 9 remain locked. No playback, recording, human listening, board, Cortex-A9, Vivado, RTL, PL or realtime acceptance occurred.
