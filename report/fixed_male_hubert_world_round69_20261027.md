# Fixed-Male HuBERT/WORLD Round 69

Status: REJECTED. The 1.65 multiscale dynamic-loss weight passed identity mean, identity P10, and UTMOS, but source leakage and CER remained above their limits.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.7054 | >= 0.45 | Pass |
| Identity P10 | 0.6786 | >= 0.35 | Pass |
| Source leakage | 0.1037 | <= 0.10 | Fail |
| UTMOS | 2.3743 | >= 2.30 | Pass |
| CER | 0.2206 | <= 0.15 | Fail |

The model used the fixed training data split (192 paired training items, 8 speaker-disjoint validation items, and target anchors from Tracks 5-8). Only male recording 4 was evaluated. The checkpoint SHA-256 is `3a045e8571e77eedacf0b408ccfb9395b1bf212bf221956a8202288dad552cca`; the PCM16 candidate SHA-256 is `c33eb00a6bf4d49de3d465dc729b562ac1143ac633675f855deda357411765d6`.

The strict evaluator ran offline with the cached Python 3.12 CPU dependencies. OpenCC was replaced by an identity compatibility shim; raw and normalized CER happened to match. The generated source transcript itself contained recognition errors, so CER remains a limited proxy for intelligibility. No recording 5 or Track 9 data was used for selection. The checkpoint was saved before the locked Track 9 read was intercepted. The newly added `--skip-locked-target-regression` option makes that boundary explicit for reruns.

Reproduction commands and exact hashes are recorded in `fixed_male_hubert_world_round69_20261027.json`. No audio was played and no board or RTL/PL state was touched.
