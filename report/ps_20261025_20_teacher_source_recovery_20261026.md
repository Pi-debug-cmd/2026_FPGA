# PS-20261025-20 Teacher Source Recovery Retry

- Date: 2026-10-26
- Role: Remote-PS-C / Codex
- Base commit: `856973c6a5dfd9f1ebc8de727330dbcb7628ad22`
- Status: BLOCKED before teacher generation, mapper training, or five-gate evaluation
- Scope: Recheck whether the approved target prompt and pinned CosyVoice source/model can be restored without substituting data or model versions.

## Approved audio and historical prompt check

The canonical Fixed-Male WAVs 1-5 and female target Tracks 5-9 are present in the checkout. The archived CosyVoice decision identifies the prompt as the first eight seconds of Track 6 and pins model revision `29e01c4e8d000f4bcd70751be16fa94bf3d85a18` and source revision `074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc`.

The archived manifest records `目标参考/target_t6_8s.wav` as 1,536,080 bytes with SHA-256 `4651ab56a9b285c0d645bd6f0b94f7987e6ed8bd5171e54c37048b436e177c8f`, but the WAV itself is not present in the checkout or the recorded legacy locations. A direct first-eight-second crop from canonical `人物音频资料/女声/Track 6.wav`, written as stereo PCM16, produced 1,536,044 bytes and SHA-256 `9755f0cfac29bd42c0628ec6707f0df7dcd09c15149a95db3d1d4729261f7361`. This does not reproduce the archived file byte-for-byte; the generated candidate is retained only under ignored `build/generated/remote_ps_c_assets/target_t6_8s_recovered.wav` and is not claimed as the historical artifact.

The current plan authorizes Track 6 as target material, so this hash mismatch alone does not invalidate the approved source. The original prompt's exact encoding/provenance remains unresolved and must not be represented as recovered.

## Pinned runtime recovery check

No CosyVoice source tree or its pinned model files were found under the task asset directory. The local HTTP proxy at `127.0.0.1:7890` has no listener and no Clash process is running. A direct read-only `git ls-remote` for the pinned CosyVoice source revision failed with `Recv failure: Connection was reset`. No alternate revision, model, or training data was used.

The official FARGAN archive, HuBERT Base, WeSpeaker, UTMOS22, Whisper-small, and the approved Fixed-Male/target WAVs remain hash-verified as recorded in the preceding recovery reports. The existing isolated environment is CPU-only PyTorch; the machine has an RTX 4060 Laptop GPU, but no CUDA-enabled task environment is available to run the pinned teacher.

## Result and next action

No teacher WAV, training pair, mapper, candidate output, or objective score was generated. This is an asset/network recovery result, not a model-quality rejection. Keep the fixed split unchanged: male 1-3 training, 4 validation, 5 locked acceptance; target Tracks 5-8 modeling, Track 9 locked holdout. Resume by restoring access to the pinned source and model, then generate source-timed native-VC teacher pairs from the approved sources using the pinned Track 6 prompt provenance. Do not inspect or use Track 9 for teacher generation, training, or selection.

Reproduction checks:

```powershell
Get-FileHash -Algorithm SHA256 'build/generated/remote_ps_c_assets/target_t6_8s_recovered.wav'
Get-NetTCPConnection -State Listen -LocalPort 7890 -ErrorAction SilentlyContinue
git -c http.proxy= ls-remote https://github.com/FunAudioLLM/CosyVoice.git 074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc
```

No playback, recording, human listening, board, Vivado, RTL, PL, Cortex-A9, or realtime work was performed.
