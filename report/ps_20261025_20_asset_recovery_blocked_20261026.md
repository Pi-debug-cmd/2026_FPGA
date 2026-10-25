# PS-20261025-20 Asset Recovery Attempt

- Date: 2026-10-26
- Role: Remote-PS-C / Codex
- Status: BLOCKED before training or evaluation
- Base commit: `ba48816b449a256bc5a331476999831b3ee444f6`
- Task branch: `agent/ymheee/PS-20261025-20`

## Scope

Attempt to restore the pinned HuBERT teacher, target FARGAN synthesis chain, evaluation assets, and isolated Python environment for the assigned HuBERT teacher-to-FARGAN computer-only quality ceiling. Fixed-Male 1-3/4/5 and target Track 5-8/9 remain the required frozen split. No hardware, audio playback, recording, or listening was performed.

## Checks and outcome

| Check | Result |
| --- | --- |
| Local task checkout | Available at the base commit; the only pre-existing worktree change was the Remote-PS-C claim in `coummucation.md`. |
| GitHub refresh | Initial fetch used the stale `127.0.0.1:7890` proxy and failed. A command-scoped direct `git fetch origin --prune` succeeded; `origin/main` remains `ba48816b449a256bc5a331476999831b3ee444f6` (PR #10 merge). PR #9 head was fetched read-only and inspected; it changes the shared `coummucation.md` among other collaboration docs. |
| Isolated Python | Installed the repository's pinned evaluation lock in Python 3.12.14, using official CPU variants `torch==2.7.1+cpu` and `torchaudio==2.7.1+cpu`; all other locked package versions were installed as pinned. CUDA was not enabled. |
| HuBERT Base | Downloaded the pinned files to `build/generated/remote_ps_c_assets/hubert_base/hubert_base`. `pytorch_model.bin` SHA-256 is `cc8c20f4b90a520757260197a3ff2505705a7adbd20ad9eeaa4e1a9b38442ef5`, matching the requirement. |
| FARGAN | The task checkout contains no runnable target FARGAN source/weights; the historical `fargan_assets.json` points to an absent `D:\Tools_FPGA\...` location. Official source/model download endpoints repeatedly reset or stalled; no replacement was used. |
| Evaluators | WeSpeaker ONNX was downloaded and matches SHA-256 `e7584940aeac8d5512d875e58ce6c09ba4ddad65d8128e1dac0d93aadd087ebb`. UTMOS22 weights and the pinned Whisper-small model weights could not be downloaded; their model snapshots are incomplete. |
| Training data | The old FARGAN/HuBERT training corpus and prepared feature manifest are not present in this checkout; only the approved Fixed-Male and target WAVs are available. The assigned teacher-to-target feature mapping cannot be trained from the missing paired corpus. |
| Audio inputs | Approved Fixed-Male 1-5 and target Track 5-9 WAV files are present in the checkout. |

## Reproduction

Run from the task checkout in PowerShell:

```powershell
git -c http.proxy= fetch origin --prune
& build/generated/remote_ps_c_env/Scripts/python.exe -c "import torch; print(torch.__version__, torch.cuda.is_available())"
Get-FileHash -Algorithm SHA256 'build/generated/remote_ps_c_assets/hubert_base/hubert_base/pytorch_model.bin'
Test-Path 'D:\Tools_FPGA\workspace\voice_conversion_zynq7020\neural_reference\Opus_FARGAN_reference\opus-main\dnn\models\fargan_sq1Ab_adv_50.pth'
```

Observed: direct fetch confirms no newer `main` commit; Torch imports as `2.7.1+cpu` with CUDA unavailable; HuBERT SHA matches; WeSpeaker SHA matches; the legacy FARGAN path returns `False`. PR #9 head is not an ancestor of current `main`, so its shared-file overlap was inspected and this branch remains based on the latest merged main. No training, inference, objective score, or quality-gate result was produced.

## Recovery conditions

1. Restore the official FARGAN source/model, pinned UTMOS and Whisper weights, and the missing teacher/paired training corpus; record and verify all hashes. The official FARGAN model SHA is `2eb56f36f71f246174d769658b5712fa81214650bd425cf050c740c8d6b4464c`; UTMOS expected SHA is `38aa51ab79e2a4e09a1449758a4b37e9cbb2e8235a49662a732d33a9ba1e9bff`.
2. Resume only after all required assets and the frozen data split are present; then train and run the assigned computer-only five-gate evaluation.

No model or audio artifact was generated. This report records an environment/asset recovery failure, not a negative model-quality result.
