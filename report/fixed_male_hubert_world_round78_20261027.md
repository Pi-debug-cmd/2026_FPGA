# Fixed-Male HuBERT/WORLD Round 78

Status: REJECTED. Doubling the VUV BCE coefficient produced a marginal UTMOS pass but did not improve CER or source leakage enough to meet the objective gates.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.6967 | >= 0.45 | Pass |
| Identity P10 | 0.6721 | >= 0.35 | Pass |
| Source leakage | 0.1134 | <= 0.10 | Fail |
| UTMOS | 2.3254 | >= 2.30 | Pass |
| CER | 0.2794 | <= 0.15 | Fail |

The checkpoint SHA-256 is `f3ebc219a32883027d26b2f1f6818545159e67351adc74d306006b0867fc891c`; candidate SHA-256 is `b2082fca1f4d73f2324085a7a54bb57903b8f3c66ae988089102a6399866ba31`. Only male recording 4 was evaluated; recording 5 and Track 9 were excluded.

The strict evaluator used an identity OpenCC compatibility shim. No audio was played and no board state was touched.
