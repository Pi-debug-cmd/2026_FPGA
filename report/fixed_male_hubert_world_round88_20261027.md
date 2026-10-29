# Fixed-Male HuBERT/WORLD Round 88

Status: REJECTED. Reducing dynamic loss weight from 1.25 to 1.20 with VUV BCE fixed at 0.35 passed identity and UTMOS but failed leakage and CER.

| Metric | Result | Gate | Pass |
|---|---:|---:|---|
| identity | 0.698881 | >=0.45 | True |
| identity_p10 | 0.676463 | >=0.35 | True |
| leakage | 0.104990 | <=0.10 | False |
| utmos | 2.328067 | >=2.30 | True |
| cer | 0.264706 | <=0.15 | False |

Best checkpoint step: 1200; completed steps: 2000. Checkpoint SHA-256: `e21d8175cb56a5aa3f3e7ac75578705b5deb8cb40fea07a5a73ef87d38586faa`. Candidate SHA-256: `a49aa55a3d9677ef42cf6d03daf63f2d4a52e451af62d3f2688c1966ea3969eb`.

Data correction: the Round25 cache explicitly declares no fixed male training audio. Its 192 public paired training rows and 8 validation rows train/select the mapping; target Tracks5-8 provide reconstruction anchors. Fixed male recordings1-3 define only the evaluator source centroid. Earlier CLAIMED wording that they were training samples is inaccurate. Only recording4 was evaluated; recording5 and Track9 were not accessed this round.

The actual evaluator used an identity OpenCC shim, despite the raw evaluator protocol string mentioning script conversion. Source text is a Whisper transcript, not verified ground truth. Scores do not establish full protocol acceptance. Training exited1 after producing its checkpoint; checkpoint history, finite weights, cache SHA and WAV SHA were checked independently. No listening or board/PS/PL/realtime result is claimed.

`build/reproduce_hubert_world_round88_20261027.py` records preparation, training, candidate and evaluation entry points with external assets. Its prepare/compile checks passed; the evaluation stage was rerun against the same candidate. Full per-window evaluation values, transcripts, best-step metadata, training history and commands are in the adjacent JSON. Weights and WAV remain ignored under build/generated.
