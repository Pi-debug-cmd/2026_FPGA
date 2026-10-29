# Public paired-teacher content audit

Status: DIAGNOSIS_ONLY; no new training. Eight public validation pairs, two speakers, verified source/teacher SHA and sample counts. Locked recording5 and targetTrack9, and development recording4, were not accessed.

| Reference | Source ASR | Teacher ASR |
|---|---:|---:|
| Corpus declared text (152 characters) | 21 edits / 13.8158% | 22 edits / 14.4737% |

| Validation stem | Source edits / chars | Teacher edits / chars | Teacher vs source ASR edits |
|---|---:|---:|---:|
| SSB04340036 | 4/20 | 4/20 | 3 |
| SSB04340089 | 7/20 | 7/20 | 5 |
| SSB04340076 | 1/20 | 1/20 | 0 |
| SSB04340118 | 0/17 | 3/17 | 3 |
| SSB00800053 | 6/20 | 5/20 | 1 |
| SSB00800102 | 3/20 | 2/20 | 3 |
| SSB00800018 | 0/20 | 0/20 | 0 |
| SSB00800067 | 0/15 | 0/15 | 0 |

The near-equal totals do not establish a clean teacher: SSB04340118 changes from source0/17 to teacher3/17. Conversely, some teacher transcriptions improve. Differences include proper names and numeric formatting (such as20% versus written Chinese), so automatic CER does not isolate conversion damage. No text was edited to improve a score. Declared text is not independently verified ground truth.

Use these same eight sentences to compare source, original teacher, compressed WORLD reconstruction, and a frozen student. This is a mechanism diagnostic, not a proposal to loosen gates or resume weight scans. The current result neither proves widespread teacher corruption nor proves that all remaining error is in the predictor. Source/teacher sample counts match, but equal durations do not establish phoneme alignment.

Offline Whisper-small, actual OpenCC0.1.7 t2s and existing punctuation rules were used. Per-sentence transcripts, hashes, counts, command and script SHA are in the adjacent JSON; process exited0. No listening, board, PS, PL or realtime result is claimed.
