# Fixed-Male HuBERT/WORLD Round 75

Status: REJECTED. Reducing target-anchor sampling probability from 0.25 to 0.15 lowered identity, did not bring leakage under its gate, and sharply worsened CER. Validation early stopping selected a checkpoint at step 1200; the training history continued through step 1600 without improvement.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.6839 | >= 0.45 | Pass |
| Identity P10 | 0.6559 | >= 0.35 | Pass |
| Source leakage | 0.1117 | <= 0.10 | Fail |
| UTMOS | 2.3876 | >= 2.30 | Pass |
| CER | 0.5000 | <= 0.15 | Fail |

The checkpoint SHA-256 is `da359e8caa8a03f27211cd1fc02a2a509e2fad50e44565365c98649c24af6104`; the PCM16 candidate SHA-256 is `23b61c5ebbab4b4a16170baca47d44f812f4e301ca8fa618d7ef878531f51623`. Only male recording 4 was evaluated. Recording 5 and Track 9 were excluded.

The strict evaluator used an identity OpenCC compatibility shim. The checkpoint was saved before the training script's subsequent Track 9 read was intercepted. No audio was played and no board state was touched.
