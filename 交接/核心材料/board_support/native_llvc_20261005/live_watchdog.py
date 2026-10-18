#!/usr/bin/env python3
"""Stop a failed live trial; conservative85C trial limit is not vendor rating."""
import os,json,time,subprocess
DIR='/home/root/native_llvc_trial_20261005/'
RUN='/run/voice-neural-live/'
def stop(reason):
    with open(RUN+'watchdog_reason.json','w') as f:json.dump(dict(reason=reason,time=time.time()),f)
    print('STOPPING_LIVE '+reason,flush=True)
    subprocess.call(['sh',DIR+'board_neural_live.sh','stop'])
def main():
    time.sleep(3)
    while True:
        for role in ['capture','convert','playback']:
            try:pid=int(open(RUN+role+'.pid').read());os.kill(pid,0)
            except (OSError,ValueError):stop('process exited: '+role);return
        root='/sys/bus/iio/devices/iio:device0/'
        try:
            t=(float(open(root+'in_temp0_raw').read())+float(open(root+'in_temp0_offset').read()))*float(open(root+'in_temp0_scale').read())/1000
            if t>=85:stop('conservative trial temperature85C reached');return
        except OSError:pass
        try:
            s=json.load(open(RUN+'status.json'))
            if s['chunks']>=770 and s['mean_compute_ms']>=13:stop('sustained compute exceeds13ms budget');return
        except (OSError,ValueError,KeyError):pass
        time.sleep(2)
if __name__=='__main__':main()
