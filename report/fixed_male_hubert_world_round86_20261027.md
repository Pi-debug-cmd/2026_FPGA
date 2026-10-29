# Fixed-Male HuBERT/WORLD Round 86

Status: REJECTED. Injecting 5% zero-mean source spectral residual did not improve CER and slightly worsened leakage and UTMOS relative to Round 85.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.7026 | >= 0.45 | Pass |
| Identity P10 | 0.6828 | >= 0.35 | Pass |
| Source leakage | 0.1021 | <= 0.10 | Fail |
| UTMOS | 2.2968 | >= 2.30 | Fail |
| CER | 0.2647 | <= 0.15 | Fail |

This was a post-processing-only round using the frozen Round85 checkpoint and gain 1.6. Candidate SHA-256 is `4da876bf25cc41250cf1d280452805d0b8fe8f863ac56c43893ef01872db61d7`; checkpoint SHA-256 is `f3fa1f9b5619ed79fc204ebc8e6e731363a4cec99d165ed60e4238f7e01c45e2`. Only male recording 4 was evaluated; recording 5 and Track 9 were excluded. No audio was played and no board state was touched.

The strict evaluator used the identity OpenCC compatibility shim. Artifacts remain under ignored `build/generated/hubert_world_round86_20261027/`.
