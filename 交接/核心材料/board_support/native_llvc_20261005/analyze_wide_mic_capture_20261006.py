"""Board-side integrity/signal summary and a bounded crop; retains full originals."""
from pathlib import Path
from array import array
import json, math, sys, hashlib
r=Path('/home/root/native_llvc_trial_20261005');prefix=r/'mic_wide_diagnostic_20261006'
meta=json.loads(Path(str(prefix)+'.json').read_text())
samples=[]
for role in ('input','output'):
 data=Path(str(prefix)+'.'+role+'.s16').read_bytes();a=array('h');a.frombytes(data)
 if sys.byteorder!='little':a.byteswap()
 assert len(a)==meta['samples']
 samples.append(a)
a,b=samples
windows=[]
for start in range(0,len(a),1600):
 values=a[start:start+1600];rms=math.sqrt(sum(float(x)*x for x in values)/max(1,len(values)))/32768
 windows.append(dict(start=start,rms=rms,peak=max((abs(x) for x in values),default=0)/32768))
rs=sorted(v['rms'] for v in windows);quiet=rs[len(rs)//5] if rs else 0
threshold=max(.012,quiet*3)
active=[w for w in windows if w['rms']>threshold]
last=active[-1]['start']+1600 if active else len(a)
end=min(len(a),last+16000);start=max(0,end-320000)
rows=[]
for role,values in zip(('input','output'),samples):
 crop=array('h',values[start:end]);raw=crop.tobytes()
 if sys.byteorder!='little':crop.byteswap();raw=crop.tobytes()
 path=r/('mic_wide_20261006_crop.'+role+'.s16');path.write_bytes(raw)
 mean=sum(crop)/max(1,len(crop));rms=math.sqrt(sum(float(x)*x for x in crop)/max(1,len(crop)))/32768
 std=math.sqrt(sum((x-mean)**2 for x in crop)/max(1,len(crop)))/32768
 rows.append(dict(role=role,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),rms=rms,std=std,peak=max((abs(x) for x in crop),default=0)/32768,clipped=sum(abs(x)>=32767 for x in crop)))
report=dict(full_record=meta,crop_start_sample=start,crop_end_sample=end,crop_seconds=(end-start)/16000,
            quiet_rms_estimate=quiet,activity_threshold=threshold,active_windows=len(active),windows=windows,
            signal_records=rows,asr_not_checked=True,speech_present_not_yet_confirmed=True,
            automatic_crop_may_include_noise_or_omit_quiet_speech=True,full_original_retained_on_board=True)
(r/'mic_wide_20261006_signal.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='windows'}))
