# Fixed-Male HuBERT/WORLD Round 87

Status: REJECTED. Reducing zero-mean source spectral residual alpha to 0.02 did not improve CER, leakage, or UTMOS over Round 85.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.7011 | >= 0.45 | Pass |
| Identity P10 | 0.6794 | >= 0.35 | Pass |
| Source leakage | 0.1011 | <= 0.10 | Fail |
| UTMOS | 2.2824 | >= 2.30 | Fail |
| CER | 0.2647 | <= 0.15 | Fail |

This was a post-processing-only round using the frozen Round85 checkpoint and gain 1.6. Candidate SHA-256 is `984939d4f10b6be67e6c147ef912ed8b9d03a986b6f7e714a506cb59961b6531`; checkpoint SHA-256 is `f3fa1f9b5619ed79fc204ebc8e6e731363a4cec99d165ed60e4238f7e01c45e2`. Only male recording 4 was evaluated; recording 5 and Track 9 were excluded. No audio was played and no board state was touched.

The strict evaluator used the identity OpenCC compatibility shim. Artifacts remain under ignored `build/generated/hubert_world_round87_20261027/`.
