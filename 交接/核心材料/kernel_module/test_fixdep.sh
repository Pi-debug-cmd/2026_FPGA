#!/bin/bash
MINGW=/d/Vivado/Vivado/2018.3/msys64/mingw64/bin
printf 'target.o: dep1.h dep2.h\n' > /tmp/t.d
echo "=== native windows path ==="
"$MINGW/fixdep.exe" 'D:\msys64\tmp\t.d' out.o 'cmdline' 2>&1 | head -6
echo "=== posix path ==="
"$MINGW/fixdep.exe" /tmp/t.d out.o 'cmdline' 2>&1 | head -6
echo "=== where is /tmp ==="
ls -la /tmp/t.d
