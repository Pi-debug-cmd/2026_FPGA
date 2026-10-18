#!/usr/bin/env python3
"""Reserve CPU1 for pinned decoder; audio helpers use CPU0 with the producer."""
import os
RUN='/run/voice-neural-live/'
DIR='/home/root/native_llvc_trial_20261005/'
for role in ['capture','playback','watchdog']:
    try:
        pid=int(open(RUN+role+'.pid').read());cmd=open('/proc/%d/cmdline'%pid,'rb').read()
        if RUN.encode() not in cmd and DIR.encode() not in cmd:raise ValueError('unexpected process')
        os.sched_setaffinity(pid,{0});print('AUDIO_CPU0 '+role+' '+str(pid),flush=True)
    except (OSError,ValueError) as e:print('AFFINITY_SKIPPED '+role+' '+str(e),flush=True)
