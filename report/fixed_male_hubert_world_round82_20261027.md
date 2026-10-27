# Fixed-Male HuBERT/WORLD Round 82

Status: REJECTED. VUV BCE 0.30 brought leakage close to its gate and UTMOS above the gate, but CER worsened substantially.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.7003 | >= 0.45 | Pass |
| Identity P10 | 0.6726 | >= 0.35 | Pass |
| Source leakage | 0.1006 | <= 0.10 | Fail |
| UTMOS | 2.3312 | >= 2.30 | Pass |
| CER | 0.2941 | <= 0.15 | Fail |

The model trained for 2000 steps. Checkpoint SHA-256 is `2d69a00d00c21674de7578c03185d325294386504fe7100e242253a04ca0fc9b`; candidate SHA-256 is `681a830407284cddb03aa1ad9c9ce6f357ac96489cc20b445375cfaaa37b7d39`. Only male recording 4 was evaluated. Recording 5 and target Track 9 were excluded.

The strict evaluator used the identity OpenCC compatibility shim. Training and candidate generation used the CPU compatibility bootstrap; the launcher returned exit code 1 after writing the artifacts, which were independently verified. No audio was played and no board state was touched.

Reproduction configuration and commands are recorded in `report/fixed_male_hubert_world_round82_20261027.json`. Runtime files and model/audio artifacts remain under ignored `build/generated/hubert_world_round82_20261027/`.
