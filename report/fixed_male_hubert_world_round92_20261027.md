# Fixed-Male HuBERT/WORLD Round 92

Status: REJECTED. GRU hidden width increases from192 to384 relative to Round88; the associated input/output linear layers resize accordingly. PCA96/input99, two layers, crop128, batch8, dynamic loss1.20, VUV BCE0.35, variance matching, source prosody, target anchor0.25, seed, early stopping and gain1.6 are unchanged.

| Metric | Result | Gate | Pass |
|---|---:|---:|---|
| identity | 0.677479 | >=0.45 | True |
| identity_p10 | 0.652369 | >=0.35 | True |
| leakage | 0.120913 | <=0.10 | False |
| utmos | 2.248302 | >=2.30 | False |
| cer | 0.382353 | <=0.15 | False |

Completed step1300; best step500, validation loss 0.7960573882. Parameters: 1841355. Checkpoint SHA-256: `457765a9bbc117dfc8316f3c105ab543f67e988241a5e7c46a48040da2381f1b`. WAV SHA-256: `a10739d25b3a668fb13cb06975b1804d0996e5218170e3727a0912efdb24ecba`.

PCA and normalizers fit192 public paired training rows;184 are eligible for crop128. Eight public validation rows select checkpoints. Target Tracks5-8 are self-reconstruction anchors. Male recordings1-3 define only the evaluation source centroid. Only recording4 was evaluated; recording5 and Track9 remain locked.

Real OpenCC0.1.7 t2s normalization is used. Raw CER is 0.3823529412; normalized CER is 0.3823529412. The source Whisper text is not manually verified ground truth. Training and candidate launchers returned1 after completion artifacts; finite weights, dimensions, history, cache SHA and WAV SHA were independently checked. Evaluation returned0. No playback, board, Cortex-A9, PL or realtime acceptance is claimed; feasibility of the larger network remains untested.

The preparation wrapper now keeps all sibling module imports within the staged runtime directory, preventing future shadowing by asset-root/build. The adjacent JSON contains runtime hashes, full history, ASR text, per-window scores and reproduction commands. Generated weights and audio remain ignored.
