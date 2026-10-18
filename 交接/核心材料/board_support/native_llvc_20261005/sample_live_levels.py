"""Collect scalar level measurements only; never microphone audio."""
import json,time
path='/run/voice-neural-live/status.json'
out='/home/root/native_llvc_trial_20261005/live_level_windows.jsonl'
last=-1
with open(out,'w') as f:
    for i in range(600):
        try:
            with open(path) as h: row=json.load(h)
            if row['chunks']!=last:
                last=row['chunks'];row['observed_unix_seconds']=time.time()
                f.write(json.dumps(row)+'\n');f.flush()
        except (IOError,ValueError,KeyError): pass
        time.sleep(1)
