import array, sys
p = sys.argv[1]
a = array.array('f')
a.frombytes(open(p, 'rb').read())
nz = sum(1 for x in a if x != 0.0)
peak = max(abs(x) for x in a)
rms = (sum(x*x for x in a)/len(a))**0.5
print("n=%d nonzero=%d peak=%.4f rms=%.4f" % (len(a), nz, peak, rms))
