# Fixed-Male HuBERT/WORLD Round 85

Status: REJECTED. Retraining with VUV BCE 0.35 brought leakage below its gate, but naturalness and CER failed.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.6997 | >= 0.45 | Pass |
| Identity P10 | 0.6769 | >= 0.35 | Pass |
| Source leakage | 0.0996 | <= 0.10 | Pass |
| UTMOS | 2.2724 | >= 2.30 | Fail |
| CER | 0.2647 | <= 0.15 | Fail |

The model trained for 2000 steps. Checkpoint SHA-256 is `f3fa1f9b5619ed79fc204ebc8e6e731363a4cec99d165ed60e4238f7e01c45e2`; candidate SHA-256 is `43fc85bcff9b5973dfe8be8168584b088ac9faff35703cfd8a0db513c752505b`. Only male recording 4 was evaluated; recording 5 and Track 9 were excluded. No audio was played and no board state was touched.

The strict evaluator used the identity OpenCC compatibility shim. Runtime artifacts remain under ignored `build/generated/hubert_world_round85_20261027/`.
