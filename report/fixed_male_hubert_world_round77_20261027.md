# Fixed-Male HuBERT/WORLD Round 77

Status: REJECTED. Removing variance matching while retaining source prosody increased leakage and worsened UTMOS and CER compared with the conditioned variance-matched route.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.6987 | >= 0.45 | Pass |
| Identity P10 | 0.6740 | >= 0.35 | Pass |
| Source leakage | 0.1451 | <= 0.10 | Fail |
| UTMOS | 2.2132 | >= 2.30 | Fail |
| CER | 0.3971 | <= 0.15 | Fail |

The checkpoint SHA-256 is `e71e7999dda6f0d2c86dd626bb1eb91b12322467b39741b46f3d5a98a60d2433`; candidate SHA-256 is `108895adf5b6e2b7ad56565671083fe649b1d4d8601dc2ea46dfd509e07e90ac`. Only male recording 4 was evaluated. Recording 5 and Track 9 were excluded.

The strict evaluator used an identity OpenCC compatibility shim. No audio was played and no board state was touched.
