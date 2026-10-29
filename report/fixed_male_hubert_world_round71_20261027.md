# Fixed-Male HuBERT/WORLD Round 71

Status: REJECTED. Returning the multiscale dynamic-loss weight to 1.55 retained identity and UTMOS gates, but leakage and content remained above their limits.

| Metric | Result | Gate | Status |
|---|---:|---:|---|
| Identity mean | 0.7055 | >= 0.45 | Pass |
| Identity P10 | 0.6785 | >= 0.35 | Pass |
| Source leakage | 0.1088 | <= 0.10 | Fail |
| UTMOS | 2.3419 | >= 2.30 | Pass |
| CER | 0.2647 | <= 0.15 | Fail |

The checkpoint SHA-256 is `4b28e786c853ed4237d5cdb17a700c0e79df736d24249cc65824ef0e80c42d88`; the PCM16 candidate SHA-256 is `734ded9562ea37a8c766218198f9f812e03bcac1c5e966946db4c1bea87a5133`. Only male recording 4 was evaluated.

The strict evaluator used the cached Python 3.12 dependencies and an identity OpenCC compatibility shim. Track 9 was excluded and the training entrypoint supports stopping immediately after checkpoint save. No audio was played and no board state was touched.
