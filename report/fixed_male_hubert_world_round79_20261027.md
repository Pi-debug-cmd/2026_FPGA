# Fixed-Male HuBERT/WORLD Round 79

Status: REJECTED. Reducing the VUV BCE coefficient improved identity and naturalness slightly, but source leakage remained over its gate and CER worsened sharply.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.7080 | >= 0.45 | Pass |
| Identity P10 | 0.6891 | >= 0.35 | Pass |
| Source leakage | 0.1088 | <= 0.10 | Fail |
| UTMOS | 2.3807 | >= 2.30 | Pass |
| CER | 0.4412 | <= 0.15 | Fail |

The checkpoint SHA-256 is `257cb1d3fa86ab61adffe06ab9258105c38384442d73addfb19f180c244fa131`; candidate SHA-256 is `4ae7617ee724798347f7528048b9d7dabac7307b2a67f6edd3c0e9712c94fcbf`. Only male recording 4 was evaluated. Recording 5 and Track 9 were excluded.

The strict evaluator used an identity OpenCC compatibility shim. No audio was played and no board state was touched.
