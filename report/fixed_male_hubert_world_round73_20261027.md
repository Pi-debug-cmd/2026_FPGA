# Fixed-Male HuBERT/WORLD Round 73

Status: REJECTED. Lowering non-F0 gain from 1.6 to 1.5 improved identity and naturalness on the Round 69 checkpoint, while source leakage increased and remained over its gate; CER remained over its gate as well.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.7224 | >= 0.45 | Pass |
| Identity P10 | 0.7013 | >= 0.35 | Pass |
| Source leakage | 0.1133 | <= 0.10 | Fail |
| UTMOS | 2.3663 | >= 2.30 | Pass |
| CER | 0.2206 | <= 0.15 | Fail |

The fixed checkpoint SHA-256 is `3a045e8571e77eedacf0b408ccfb9395b1bf212bf221956a8202288dad552cca`; candidate SHA-256 is `0a24d19c018b155546131ab962032fe0f5d9d591c4ee32cebd8b08ad9a339ba2`. Only male recording 4 was evaluated. Track 9 and recording 5 remained excluded.

The strict evaluator used an identity OpenCC compatibility shim. No audio was played and no board state was touched.
