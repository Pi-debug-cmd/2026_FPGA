# Public validation content-chain diagnosis

Frozen Round88 checkpoint, gain1.6; no new training and no parameter selection. Same eight public validation sentences, declared reference152 characters, offline Whisper-small with real OpenCC0.1.7.

| Stage | Edits | Micro CER |
|---|---:|---:|
| source | 21/152 | 0.138158 |
| teacher | 22/152 | 0.144737 |
| world5 | 24/152 | 0.157895 |
| world20 | 25/152 | 0.164474 |
| student_gain1_6 | 44/152 | 0.289474 |

| Stem | Teacher | WORLD5ms | Cached20ms | Student+gain1.6 |
|---|---:|---:|---:|---:|
| SSB04340036 | 4 | 5 | 5 | 7 |
| SSB04340089 | 7 | 9 | 7 | 13 |
| SSB04340076 | 1 | 1 | 3 | 1 |
| SSB04340118 | 3 | 2 | 3 | 9 |
| SSB00800053 | 5 | 5 | 5 | 7 |
| SSB00800102 | 2 | 2 | 2 | 4 |
| SSB00800018 | 0 | 0 | 0 | 2 |
| SSB00800067 | 0 | 0 | 0 | 1 |

The largest observed increase occurs between cached-WORLD reconstruction and the student inference pipeline:25 to44 edits. Increasing temporal compression from5ms to20ms changes only24 to25 edits in aggregate. This supports prioritizing mapping/alignment/inference diagnostics over another crop/PCA/width sweep. It does not establish a causal additive decomposition: ASR errors can change non-monotonically, and the student branch also includes clipping and contrast recovery.

WORLD5 and20 branches use true teacher parameters with broad bounds, but still apply existing synthesis median filters, VUV threshold and peak normalization. The student uses frozen Round88 prediction, gain1.6 and target-anchor bounds. Anchor bounds use5ms target features rather than the20ms interpolation in production candidate generation; no bit-identical reproduction of the recording4 result is claimed. Teacher raw transcripts are reused from the previous audit only after matching source/teacher hashes.

Both public speakers are retained in adjacent JSON, together with transcripts, per-output hashes, checkpoint/cache/corpus hashes, synthesis metadata and commands. Generation exited1 after producing all24 WAV and8-row manifest; evaluation exited0. WAV hashes were checked before evaluation and again before reporting. Files remain ignored under build/generated.

Declared text has not been independently manually verified. Numeric formatting and proper names affect CER. These eight sentences do not prove fixed-male generalization or target sound acceptance. No recording4/5 or Track9 audio, new training, playback, board, PS, PL or realtime test was used.

Next: measure source-to-teacher time alignment on these same nonlocked pairs, and quantify clipping/dynamic errors before deciding whether to repair supervised alignment, target representation, or the mapping objective. Do not resume dropout or weight scans based only on these aggregate numbers.
