import mmap, struct, array
PHYS = 0x30500000
SIZE = 8*1024*1024
f = open('/dev/mem', 'rb')
m = mmap.mmap(f.fileno(), SIZE, offset=PHYS, access=mmap.ACCESS_READ)

def rd(off, n):
    return m[off:off+n]

# group layout (bytes)
N_W=16; W_STRIDE=262144
GIO = 26*512 + 26*512*4
in0 = N_W*W_STRIDE
out0 = in0 + 26*512
in1 = N_W*W_STRIDE + GIO
out1 = in1 + 26*512
print("in0=%08x out0=%08x in1=%08x out1=%08x" % (PHYS+in0, PHYS+out0, PHYS+in1, PHYS+out1))

# group1 input first 16 bytes (deterministic pattern for matrix6: t=0,k=0..15)
print("in1 first16:", list(rd(in1,16)))
# expected for mi=6,t=0: (0*17+k*11+6*7)%255-127
exp = [((k*11+42)%255)-127 for k in range(16)]
print("expected   :", exp)

# group1 output first 8 int32
o = array.array('i'); o.frombytes(rd(out1, 32))
print("out1 int32 :", list(o))
# group0 output first 8 int32 for comparison (matrix5 last group0 run)
o0 = array.array('i'); o0.frombytes(rd(out0,32))
print("out0 int32 :", list(o0))
