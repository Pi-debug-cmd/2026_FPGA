# PS-20261025-20 Pinned FARGAN Asset Recovery

- Date: 2026-10-26
- Role: Remote-PS-C / Codex
- Base commit: ba48816b449a256bc5a331476999831b3ee444f6 (PR #10 merge)
- Branch: agent/ymheee/PS-20261025-20; draft PR #11
- Status: BLOCKED before teacher-to-target training or five-gate evaluation

## Recovered official asset

The Xiph Opus main source archive cached at build/generated/remote_ps_c_assets/opus_fargan_main_20261026.zip contains autogen.sh, which requests opus_data-a5177ec6fb7d15058e99e57029746100121f68e4890b1467d4094aa336b6013e.tar.gz from https://media.xiph.org/opus/models/. The archive was downloaded to the ignored D: task asset directory and its SHA-256 matches the checksum in the upstream script.

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| Opus model archive | 134674421 | a5177ec6fb7d15058e99e57029746100121f68e4890b1467d4094aa336b6013e |
| dnn/models/fargan_sq1Ab_adv_50.pth | 13775086 | 2eb56f36f71f246174d769658b5712fa81214650bd425cf050c740c8d6b4464c |
| dnn/fargan_data.c | 21978624 | 68ba6e8731007f7184be862d7d1afe4cef096a7c9bcbfa115962340f725e004c |
| dnn/fargan_data.h | 1844 | 402e691f4975d6d156903f0fe12da3385e20ec6dd6155c3387e9dad536f654cd |

The model and C assets were extracted under ignored build/generated/remote_ps_c_assets/opus_official/. Their hashes match the previously recorded 交接/核心材料/board_support/native_llvc_20261005/fargan_assets.json. No FARGAN executable was built or run. No model, audio, or archive was added to Git.

## Reproduction

From the task checkout, download https://media.xiph.org/opus/models/opus_data-a5177ec6fb7d15058e99e57029746100121f68e4890b1467d4094aa336b6013e.tar.gz to build/generated/remote_ps_c_assets/opus_data-a5177ec6.tar.gz. If required by the host network, use FlClash HTTP proxy 127.0.0.1:7890. Then run Get-FileHash -Algorithm SHA256 build/generated/remote_ps_c_assets/opus_data-a5177ec6.tar.gz and compare to the table. The archive members can be checked with Python tarfile and hashlib.sha256; their byte counts and digests must also match the table.

## Remaining gate

HuBERT Base and WeSpeaker were verified in the prior report. The frozen source/target WAVs are present, but the historical paired teacher-feature training corpus and manifest are absent. The pinned UTMOS and Whisper-small weights are incomplete. The existing target FARGAN oracle is only a vocoder reconstruction ceiling; it cannot replace the missing HuBERT-to-target mapping. No training, inference, five-gate score, or quality conclusion is claimed. No board, Vivado, RTL, PL, realtime, playback, recording, or human-listening work was done. Restore the remaining approved assets with provenance and hashes before resuming the assigned computer-side evaluation.

## Additional evaluator asset recovered

The pinned UTMOS22 Strong weight was downloaded from the exact URL in `交接/核心材料/neural_reference/cross_evaluators/manifest.json` into the ignored D: task asset directory.

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `utmos22_strong_step7459_v1.pt` | 411179119 | `38aa51ab79e2a4e09a1449758a4b37e9cbb2e8235a49662a732d33a9ba1e9bff` |

The digest and byte count match the project manifest. Whisper-small remains incomplete. Its frozen revision is `973afd24965f72e36ca33b3055d56a652f456b4d`; existing local Hugging Face entries are `.incomplete` and are not accepted as an evaluator. The approved paired HuBERT/target-FARGAN training feature corpus and manifest remain absent. No training, inference, or five-gate evaluation has run.
