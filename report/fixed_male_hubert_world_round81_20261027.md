# Fixed-Male HuBERT/WORLD Round 81

Status: REJECTED. Reducing the VUV BCE coefficient to 0.40 slightly reduced leakage, but UTMOS fell below its gate and CER remained above its gate.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.7020 | >= 0.45 | Pass |
| Identity P10 | 0.6843 | >= 0.35 | Pass |
| Source leakage | 0.1140 | <= 0.10 | Fail |
| UTMOS | 2.2540 | >= 2.30 | Fail |
| CER | 0.2353 | <= 0.15 | Fail |

The model trained for 2000 steps; the best validation checkpoint was selected from the training history. Checkpoint SHA-256 is `3640730e8c350277688aeaea43391f0c355d5b421cc67b935ceb56df7be9aaa4`; candidate SHA-256 is `7ecdeba5335682dbb7226fb12e84ad306b7b4140c33083b0d3c2fa30189b2fad`. Only male recording 4 was evaluated. Recording 5 and target Track 9 were excluded.

The strict evaluator used the identity OpenCC compatibility shim. Training ran on CPU with the cached dependency bootstrap and the torchvision NMS compatibility schema. No audio was played and no board state was touched.

Reproduction configuration and commands are recorded in `report/fixed_male_hubert_world_round81_20261027.json`. Runtime files and model/audio artifacts remain under ignored `build/generated/hubert_world_round81_20261027/`.
