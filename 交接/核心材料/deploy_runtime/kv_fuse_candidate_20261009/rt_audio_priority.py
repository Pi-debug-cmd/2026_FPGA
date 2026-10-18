"""Temporary live-test scheduling experiment; affects only running PIDs."""
import os
from pathlib import Path

run = Path("/run/kvf-native32")
for role, priority in (("capture", 8), ("down", 5), ("up", 5), ("playback", 8)):
    pid = int((run / f"{role}.pid").read_text().strip())
    os.sched_setscheduler(pid, os.SCHED_FIFO, os.sched_param(priority))
    print(f"{role} pid={pid} sched={os.sched_getscheduler(pid)} priority={priority}")
