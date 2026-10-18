"""Compare board-produced float32 PCM with the host int8 reference."""
import math
import struct
import sys
import zlib

expected = zlib.decompress(open(sys.argv[1], 'rb').read())
actual = open(sys.argv[2], 'rb').read()
assert 0 < len(actual) <= len(expected) and len(actual) % 4 == 0
expected = expected[:len(actual)]
n = len(actual) // 4
ex = struct.iter_unpack('<f', expected)
ac = struct.iter_unpack('<f', actual)
sx = sy = sxx = syy = sxy = se = max_error = 0.0
for (x,), (y,) in zip(ex, ac):
    sx += x
    sy += y
    sxx += x*x
    syy += y*y
    sxy += x*y
    error = abs(x-y)
    se += error*error
    max_error = max(max_error, error)
cov = sxy/n - sx*sy/(n*n)
vx = sxx/n - (sx/n)**2
vy = syy/n - (sy/n)**2
print('samples=%d correlation=%.9f rmse=%.9f max_error=%.9f board_rms=%.7f' %
      (n, cov/math.sqrt(vx*vy), math.sqrt(se/n), max_error, math.sqrt(syy/n)))
