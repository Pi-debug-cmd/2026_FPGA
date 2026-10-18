#!/bin/bash
echo "=== gcc target ==="; gcc -dumpmachine
echo "=== errno test ==="
printf '#include <errno.h>\nint main(){return errno;}\n' > /tmp/e.c
gcc /tmp/e.c -o /tmp/e.exe 2>&1 && echo ERRNO_LINK_OK || echo ERRNO_LINK_FAIL
echo "=== iob test ==="
printf '#include <stdio.h>\nint main(){return fputc(65,stdout);}\n' > /tmp/s.c
gcc /tmp/s.c -o /tmp/s.exe 2>&1 && echo IOB_LINK_OK || echo IOB_LINK_FAIL
