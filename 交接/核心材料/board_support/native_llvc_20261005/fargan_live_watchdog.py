#!/usr/bin/env python3
"""Stop hot trial; restore accepted wide baseline for other runtime failures."""
import os,json,time,subprocess
DIR='/home/root/native_llvc_trial_20261005/'
RUN='/run/voice-neural-live/'
def failed(reason,restore=True):
    report=dict(reason=reason,time=time.time(),restore_wide_baseline=restore)
    diagnostics={}
    for name in ['capture.log','convert.log','playback.log','watchdog.log','status.json']:
        try:diagnostics[name]=open(RUN+name).read()[-8192:]
        except OSError:pass
    with open(DIR+'fargan_last_failure_logs.json','w') as f:json.dump(dict(report,diagnostics=diagnostics),f)
    with open(DIR+'fargan_last_watchdog_reason.json','w') as f:json.dump(report,f)
    try:
        if int(open(RUN+'watchdog.pid').read())==os.getpid():os.unlink(RUN+'watchdog.pid')
    except (OSError,ValueError):pass
    subprocess.call(['sh',DIR+'board_neural_fargan.sh','stop'])
    if restore:subprocess.call(['sh',DIR+'board_neural_wide192.sh','start'])
def main():
    time.sleep(3);last_frames=-1;last_progress=time.monotonic();underruns0=None
    while True:
        for role in ['capture','convert','playback']:
            try:
                pid=int(open(RUN+role+'.pid').read());os.kill(pid,0)
                cmd=open('/proc/%d/cmdline'%pid,'rb').read()
                if DIR.encode() not in cmd and RUN.encode() not in cmd:raise ValueError('pid belongs to another process')
            except (OSError,ValueError):failed('process invalid: '+role);return
        root='/sys/bus/iio/devices/iio:device0/'
        try:
            temp=(float(open(root+'in_temp0_raw').read())+float(open(root+'in_temp0_offset').read()))*float(open(root+'in_temp0_scale').read())/1000
            if temp>=85:failed('conservative trial85C limit reached',False);return
        except OSError:pass
        try:
            s=json.load(open(RUN+'status.json'));frames=s['frames']
            if frames!=last_frames:last_frames=frames;last_progress=time.monotonic()
            if frames>=1000 and (s['mean_compute_ms']>=10 or s['compute_deadlines_missed']/frames>.05):failed('sustained compute exceeds trial budget');return
        except (OSError,ValueError,KeyError):pass
        if time.monotonic()-last_progress>6:failed('no conversion progress for6seconds');return
        try:
            count=open(RUN+'playback.log').read().count('underrun')
            if underruns0 is None:underruns0=count
            elif count-underruns0>2:failed('repeated playback underruns');return
        except OSError:pass
        time.sleep(2)
if __name__=='__main__':main()
