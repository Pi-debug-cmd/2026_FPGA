# Fixed-Male HuBERT/WORLD Round 80

Status: REJECTED. A VUV BCE coefficient of 0.50 kept UTMOS above its gate and improved CER over Round 79, but source leakage and CER still failed.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.7022 | >= 0.45 | Pass |
| Identity P10 | 0.6817 | >= 0.35 | Pass |
| Source leakage | 0.1142 | <= 0.10 | Fail |
| UTMOS | 2.3071 | >= 2.30 | Pass |
| CER | 0.2353 | <= 0.15 | Fail |

The model trained for 2000 steps; its best validation checkpoint was at step 1200. Checkpoint SHA-256 is `de268f4a915970f8dbe0298696301cd0b88dded3160eefbaffa27bde68d8a9ca`; candidate SHA-256 is `ee897bca071686a624f5631a0322238b0d1988cc9f7452900bdbb85d1d0b4c91`. Training used the Round 25 cache manifest (`4d34669259834bd30219f34af4730712c9aa7c4cf8fa8bc3c5ccde9ee3cc5bc5`) and frozen corpus manifest (`2404ce8282ec2759d4edabd32d7d3e8068d7b69c835194616fe121ec3015fabb`).

Only male recording 4 was evaluated. Recording 5 and target Track 9 were excluded. The strict evaluator used the identity OpenCC shim, so Chinese script normalization is limited. Training ran on CPU because CUDA was unavailable; a runtime compatibility bootstrap defined the absent torchvision NMS schema. The launcher emitted the completed checkpoint record but returned exit code 1 after writing it; the checkpoint was subsequently loaded and its format, best step, cache SHA, and history verified. No audio was played and no board state was touched.

Reproduction configuration and commands are recorded in `report/fixed_male_hubert_world_round80_20261027.json`. Round-specific runtime files and model/audio artifacts remain under ignored `build/generated/hubert_world_round80_20261027/`.
