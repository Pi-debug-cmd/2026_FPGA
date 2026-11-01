# SUBMIT-20261101-01: AMD Round30 Submission Package

## Source and package identity

- Task: `SUBMIT-20261101-01`.
- Source implementation: `PL-20261027-01` Round30 commit `a8f6f8f32b159eaea277354118220c633f31fbc2`.
- Later source branch head inspected only to establish provenance: `6f0d68ba367c920afbef2aa7f7265a5d0176edd3`. Round31-34 synthesis-pulse experiments are not included.
- Public package repository: `https://github.com/Pi-debug-cmd/amd-zynq-world-voice-pl-2026`.
- Latest package commit: `bc1c51c4bc7e329a0a84bd94ff9773ec69f82385` (initial package commit: `ed7bebfc83a8453e5ea3ea7a355c4cee573e2c89`).
- Package: 78 files, 6,323 lines; English-only directory and file names.

## Contents

The repository includes the Round30 HLS kernel, PS streaming runtime and backend, Linux DMA driver, persistent boot/install/recovery scripts, Vivado/HLS and ARM build scripts, deterministic testbench, unit checks, design/interface/hardware/reproduction documentation, competition metrics, rounds 16-30 evidence, and the Vivado MCP/Git/GitHub workflow Skill.

The 2026 AMD guide's autonomous-topic section 3.3 permits PS software and RTL/HLS combinations on Zynq-7000; PYNQ is recommended for the beginner group but is not required. The package describes the implementation honestly as PetaLinux C++ PS plus HLS PL, not PYNQ.

## Checks

- `python -m unittest sim.test_world_minphase_boot -v`: 2 passed, 2 skipped because Windows has no POSIX `sh` executable. The skipped cases are shell failure-injection checks; they require a POSIX host or board BusyBox shell.
- `python metrics/scripts/validate_metrics.py`: 18 metric rows and all referenced evidence files present.
- `python -m py_compile metrics/scripts/validate_metrics.py sim/test_world_minphase_boot.py`: passed.
- `git diff --cached --check`: passed before the package commit.
- SHA comparison: 20 selected HLS, PS, driver, build, and boot source files exactly match their Git blobs at the Round30 implementation commit.
- Vivado/HLS rebuild and new board testing were not run during packaging.

## Evidence boundary and remaining work

Round30 proves candidate persistence across a normal reboot, `READY_CANDIDATE`, active capture/playback PCM, and PL calls increasing from 2,278 to 13,751. It does not prove long-duration stability, prompt audibility, full-WORLD-in-PL, final conversion quality, target identity, or unseen-speaker generalization. Round23 is a bounded 20-second audible test; Round24 is an invalid no-speech stability trial; Round21's initial audibility rejection remains in the evidence set.

The source repository did not provide the complete vendor audio base project, PetaLinux image, or tracked generated `.bit`/`.xsa`/`.hwh` artifacts. Full clean-room system rebuild, artifact regeneration, valid 30-minute speech stability, end-to-end P95/P99 latency, final voice-quality acceptance, and any contest-specific demo material remain open. Human speech and generated audio were omitted because they are not required for the HLS build or deterministic kernel test and the source recordings are controlled assets.

## Reproduction entry points

See the public repository's `README.md`, `docs/reproduction.md`, and `SUBMISSION_CHECKLIST.md`. The most useful host checks are:

```sh
python -m unittest sim.test_world_minphase_boot -v
python metrics/scripts/validate_metrics.py
```
