# Fixed-Male HuBERT/WORLD Round 76

Status: REJECTED. Removing source prosody from the input increased source leakage and worsened naturalness and CER. This isolates source-prosody conditioning as a useful leakage restraint in the current model, although the conditioned route still has not met all gates.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.6860 | >= 0.45 | Pass |
| Identity P10 | 0.6648 | >= 0.35 | Pass |
| Source leakage | 0.1611 | <= 0.10 | Fail |
| UTMOS | 2.1773 | >= 2.30 | Fail |
| CER | 0.4118 | <= 0.15 | Fail |

The checkpoint SHA-256 is `6d3c276ad5345a0ea5302191476ba446d95615d7ba41e4174582c63b58d36cb8`; candidate SHA-256 is `b2a7afe0414eba2a0e4a2c5fb46259c70de38927d9fa97f2eabf2f2497ed964b`. Only male recording 4 was evaluated; recording 5 and Track 9 were excluded.

The strict evaluator used an identity OpenCC compatibility shim. No audio was played and no board state was touched.
