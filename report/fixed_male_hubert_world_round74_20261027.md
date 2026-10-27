# Fixed-Male HuBERT/WORLD Round 74

Status: REJECTED. Lowering non-F0 gain to 1.3 further increased target identity, but source leakage rose to 0.1355, UTMOS fell below its gate, and CER worsened.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.7450 | >= 0.45 | Pass |
| Identity P10 | 0.7298 | >= 0.35 | Pass |
| Source leakage | 0.1355 | <= 0.10 | Fail |
| UTMOS | 2.2570 | >= 2.30 | Fail |
| CER | 0.3824 | <= 0.15 | Fail |

The fixed checkpoint SHA-256 is `3a045e8571e77eedacf0b408ccfb9395b1bf212bf221956a8202288dad552cca`; candidate SHA-256 is `23d30e3e30f1dd22ef5308c68a1074ba3d09356c4d0e3f4932049b5eee173ac5`. Only male recording 4 was evaluated. Track 9 and recording 5 were excluded.

The strict evaluator used an identity OpenCC compatibility shim. No audio was played and no board state was touched.
