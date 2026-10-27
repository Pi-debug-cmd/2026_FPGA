# Fixed-Male HuBERT/WORLD Round 70

Status: REJECTED. Raising the multiscale dynamic-loss weight from 1.65 to 1.70 reduced identity and naturalness slightly; source leakage and CER still failed.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.7009 | >= 0.45 | Pass |
| Identity P10 | 0.6733 | >= 0.35 | Pass |
| Source leakage | 0.1046 | <= 0.10 | Fail |
| UTMOS | 2.3363 | >= 2.30 | Pass |
| CER | 0.2647 | <= 0.15 | Fail |

Only male recording 4 was evaluated. The checkpoint SHA-256 is `a297ea51273b137f0a65924d6c4cbc092f6a253da83b8373cb6fac23ca20f236`; the PCM16 candidate SHA-256 is `a4ffd96e0c41a3dffc6cc8560a22c8dd936fc99b296219518bb5a504bd6598ae`.

The strict evaluator used the cached Python 3.12 dependencies and an identity OpenCC compatibility shim. The training boundary now supports `--skip-locked-target-regression`, which saves the checkpoint and returns before accessing Track 9. No recording 5, audio playback, or board operation was involved.
