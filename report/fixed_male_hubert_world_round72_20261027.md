# Fixed-Male HuBERT/WORLD Round 72

Status: REJECTED. The 1.45 multiscale dynamic-loss weight had the lowest leakage among the recent weight trials, but leakage remained over its gate and CER did not improve.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.7045 | >= 0.45 | Pass |
| Identity P10 | 0.6792 | >= 0.35 | Pass |
| Source leakage | 0.1028 | <= 0.10 | Fail |
| UTMOS | 2.3635 | >= 2.30 | Pass |
| CER | 0.2647 | <= 0.15 | Fail |

The checkpoint SHA-256 is `8cc81ef4e25ca63c7d1df36a64bf737ffaa53cd7fef9564a05fc2156f9fadd4b`; the PCM16 candidate SHA-256 is `03c4e244c53dd9c46065796c006fd9d1bf6ecbb7025a13f6649ba52d7c051394`. Only male recording 4 was evaluated. Track 9 and recording 5 remained excluded.

The evaluator used the cached Python 3.12 dependencies and an identity OpenCC compatibility shim. No audio was played and no board state was touched.
