# Fixed-Male HuBERT/WORLD Round 83

Status: REJECTED. Mixing 10% source VUV lowered leakage below its gate and improved UTMOS, but CER worsened.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.6990 | >= 0.45 | Pass |
| Identity P10 | 0.6764 | >= 0.35 | Pass |
| Source leakage | 0.0993 | <= 0.10 | Pass |
| UTMOS | 2.3515 | >= 2.30 | Pass |
| CER | 0.3235 | <= 0.15 | Fail |

This was a post-processing-only round using the frozen Round82 checkpoint and gain 1.6. The candidate SHA-256 is `746879f49f330f33e81facfe133f3eeb7c581281f2682a457167b29b5bf9c404`; the frozen Round82 checkpoint SHA-256 is `2d69a00d00c21674de7578c03185d325294386504fe7100e242253a04ca0fc9b`. Only male recording 4 was evaluated; recording 5 and Track 9 were excluded.

The strict evaluator used the identity OpenCC compatibility shim. No audio was played and no board state was touched.

Reproduction configuration and commands are recorded in `report/fixed_male_hubert_world_round83_20261027.json`. Candidate artifacts remain under ignored `build/generated/hubert_world_round83_20261027/`.
