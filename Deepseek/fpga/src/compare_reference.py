"""Bit-exact Python model of axis_pitch_shift.v and comparison with board output.

Same integer semantics as src/reference/pitch_shift_fixed.py (which was already
verified sample-by-sample against the RTL), but pure Python (no numpy on the host
guarantee) and reading raw PCM16 files.
"""
import struct
import sys
from pathlib import Path

Q = 1 << 16
WINDOW = 1024
DEPTH = 2048
PHASE_MASK = WINDOW * Q - 1


def pitch_shift(samples, ratio_q16):
    buf = [0] * DEPTH
    wi = 0
    phase = 0
    out = []
    append = out.append
    for s in samples:
        buf[wi] = s
        if ratio_q16 == Q:
            append(s)
        else:
            weight = (phase >> 9) if phase < WINDOW * Q // 2 else (2 * Q - (phase >> 9))
            other = phase ^ (WINDOW * Q // 2)
            r0 = (wi - 2 - (phase >> 16)) & (DEPTH - 1)
            f0 = phase & (Q - 1)
            t0 = (buf[r0] * (Q - f0) + buf[(r0 - 1) & (DEPTH - 1)] * f0) >> 16
            r1 = (wi - 2 - (other >> 16)) & (DEPTH - 1)
            f1 = other & (Q - 1)
            t1 = (buf[r1] * (Q - f1) + buf[(r1 - 1) & (DEPTH - 1)] * f1) >> 16
            append((t0 * weight + t1 * (Q - weight)) >> 16)
            phase = (phase + Q - ratio_q16) & PHASE_MASK
        wi = (wi + 1) & (DEPTH - 1)
    return out


def main():
    inp = Path(sys.argv[1]).read_bytes()
    outp = Path(sys.argv[2]).read_bytes()
    ratio = int(sys.argv[3])
    if len(inp) % 2 or len(outp) % 2:
        raise SystemExit('odd byte count')
    samples = list(struct.unpack('<%dh' % (len(inp) // 2), inp))
    actual = list(struct.unpack('<%dh' % (len(outp) // 2), outp))
    if len(samples) != len(actual):
        raise SystemExit('length mismatch in=%d out=%d' % (len(samples), len(actual)))
    expect = pitch_shift(samples, ratio)
    expect16 = [((v + 32768) & 0xffff) - 32768 for v in expect]
    diffs = [abs(a - b) for a, b in zip(actual, expect16)]
    bad = [i for i, d in enumerate(diffs) if d > 2]
    print('samples', len(samples), 'ratio_q16', ratio)
    print('max_abs_diff', max(diffs) if diffs else 0)
    print('samples_diff_gt0', sum(1 for d in diffs if d > 0))
    print('samples_diff_gt2', len(bad))
    print('first_16_in', samples[:8])
    print('first_16_expected', expect16[:8])
    print('first_16_actual', actual[:8])
    ones = sum(1 for d in diffs if d == 1)
    twos = sum(1 for d in diffs if d == 2)
    print('diff_hist_1', ones, 'diff_hist_2', twos)
    print('VERDICT', 'PASS' if not bad else 'FAIL')
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())
