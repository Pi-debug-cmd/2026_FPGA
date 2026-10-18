"""Reuse the heard audio routes with fresh v2 configure/reset before each run."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
s = (root / 'board/live_pitch_low_latency_trial.sh').read_text(encoding='utf-8')
s = s.replace('RATIO=${1:-65536}', 'RATIO=${1:-86856}')
s = s.replace('BIN=/tmp/codex_pitch_fixed', 'BIN=/tmp/codex_pl_control_20261011/pitch_dma_stream')
s = s.replace('RUN=/tmp/codex_pitch_trial_v5_${RATIO}',
              '''TAG=${3:-}
case "$TAG" in *[!a-zA-Z0-9_]*) echo "invalid trial tag" >&2; exit 2;; esac
RUN=/tmp/codex_pitch_control_trial_${RATIO}_${SECONDS_TO_RUN}${TAG:+_$TAG}''')
s = s.replace('[ "$SECONDS_TO_RUN" -le 60 ]', '[ "$SECONDS_TO_RUN" -le 600 ]')
s = s.replace('"$BIN" "$RATIO" native_s24', '"$BIN" 256 native_s24 "$RATIO"')
s = s.replace('# Finite PS-only trial.', '# Finite v2 PL DMA trial; configure/reset before capture processing.')
(root / 'board/live_pitch_control_trial.sh').write_text(s, encoding='utf-8', newline='\n')
print('Generated finite configurable PL audio trial')
