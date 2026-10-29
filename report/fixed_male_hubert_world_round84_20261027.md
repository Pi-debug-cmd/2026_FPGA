# Fixed-Male HuBERT/WORLD Round 84

Status: REJECTED. Reducing source VUV mixing from 0.10 to 0.05 improved CER relative to Round 83, but leakage remained just above the gate and CER remained far above the gate.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.7012 | >= 0.45 | Pass |
| Identity P10 | 0.6747 | >= 0.35 | Pass |
| Source leakage | 0.1005 | <= 0.10 | Fail |
| UTMOS | 2.3238 | >= 2.30 | Pass |
| CER | 0.2500 | <= 0.15 | Fail |

This was a post-processing-only round using the frozen Round82 checkpoint and gain 1.6. The candidate SHA-256 is `1d7320b567dd30f41dcdc7b1a96049146c8dca8c3efdbd9c05334185fd62e4c1`; checkpoint SHA-256 is `2d69a00d00c21674de7578c03185d325294386504fe7100e242253a04ca0fc9b`. Only male recording 4 was evaluated; recording 5 and Track 9 were excluded. No audio was played and no board state was touched.

The strict evaluator used the identity OpenCC compatibility shim. Reproduction details are in `report/fixed_male_hubert_world_round84_20261027.json`; artifacts remain under ignored `build/generated/hubert_world_round84_20261027/`.
