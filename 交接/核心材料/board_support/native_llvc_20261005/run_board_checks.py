#!/usr/bin/env python3
"""Actual board inference; preserve raw samples, no quality/real-time approval."""
import os,sys,time,math,array,json,hashlib,struct,subprocess
ROOT='/home/root/native_llvc_trial_20261005'
def path(name):return ROOT+'/'+name
def readarray(name,kind):
    a=array.array(kind)
    with open(path(name),'rb') as f:a.frombytes(f.read())
    return a
def savearray(name,a):
    with open(path(name),'wb') as f:f.write(a.tobytes())
def temperature():
    root='/sys/bus/iio/devices/iio:device0/'
    try:
        raw=float(open(root+'in_temp0_raw').read());offset=float(open(root+'in_temp0_offset').read());scale=float(open(root+'in_temp0_scale').read())
        return (raw+offset)*scale/1000
    except Exception:return None
def writejson(name,data):
    with open(path(name),'w') as f:json.dump(data,f,indent=2)
def sha(name):
    h=hashlib.sha256()
    with open(path(name),'rb') as f:
        while True:
            b=f.read(1048576)
            if not b:break
            h.update(b)
    return h.hexdigest()
def native(input_name,output_name):
    before=temperature();begin=time.monotonic()
    child=subprocess.Popen([path('native_llvc_arm'),path('llvc_step20.f32'),path(input_name),path(output_name)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    peak=before
    try:
        while child.poll() is None:
            time.sleep(.25);t=temperature()
            if t is not None:peak=t if peak is None else max(peak,t)
            if t is not None and t>=85:raise RuntimeError('conservative trial cutoff85C, not manufacturer rating')
            if time.monotonic()-begin>180:raise RuntimeError('180s native trial timeout')
    except Exception:
        child.kill();child.communicate();raise
    out,err=child.communicate()
    if child.returncode:raise RuntimeError('native exit '+str(child.returncode)+' '+err.decode(errors='replace'))
    stats=json.loads(out.decode());stats.update(wall_seconds=time.monotonic()-begin,temperature_before_c=before,temperature_peak_c=peak,
        binary_sha256=sha('native_llvc_arm'),model_sha256=sha('llvc_step20.f32'),actual_arm_execution=True)
    return stats
def numerical():
    rows=[]
    for name in ['silence_416','tone_1000','edge_209','real_16000']:
        stats=native(name+'.input.f32',name+'.arm.f32')
        a=readarray(name+'.torch.f32','f');b=readarray(name+'.arm.f32','f')
        if len(a)!=len(b) or len(a)!=stats['samples']:raise RuntimeError('sample length mismatch')
        if not all(math.isfinite(v) for v in b):raise RuntimeError('nonfinite output')
        squared=sum((float(x)-float(y))**2 for x,y in zip(a,b));energy=sum(float(x)**2 for x in a)
        ratio=math.sqrt(squared/max(energy,1e-24));maximum=max(abs(x-y) for x,y in zip(a,b)) if len(a) else 0
        row=dict(case=name,native=stats,normalized_rmse=ratio,max_absolute_error=maximum,
                 output_sha256=sha(name+'.arm.f32'),migration_pass=ratio<1e-3 and maximum<1e-3)
        rows.append(row);print(json.dumps(row),flush=True)
        writejson('actual_arm_numerical_checks.json',dict(cases=rows,all_passed=all(r['migration_pass'] for r in rows),
             speech_quality_accepted=False,continuous_real_time_verified=False))
        if not row['migration_pass']:raise RuntimeError('actual ARM migration mismatch')
def wav(name,samples):
    pcm=array.array('h',(max(-32768,min(32767,int(round(float(x)*32767)))) for x in samples)).tobytes()
    header=struct.pack('<4sI4s4sIHHIIHH4sI',b'RIFF',36+len(pcm),b'WAVE',b'fmt ',16,1,1,16000,32000,2,16,b'data',len(pcm))
    with open(path(name),'wb') as f:f.write(header);f.write(pcm)
def capture():
    raw=readarray('mic_16k_s16.raw','h');source=array.array('f',(v/32768.0 for v in raw))
    if len(source)!=5*16000:raise RuntimeError('capture must be5s/mono16k signed16')
    savearray('mic_16k.f32',source);wav('mic_original.wav',source)
    source_rms=math.sqrt(sum(v*v for v in source)/len(source));source_peak=max(abs(v) for v in source)
    stats=native('mic_16k.f32','mic_converted_raw.f32');result=readarray('mic_converted_raw.f32','f')
    if len(result)!=len(source) or not all(math.isfinite(v) for v in result):raise RuntimeError('converted output invalid')
    rms=math.sqrt(sum(v*v for v in result)/len(result));peak=max(abs(v) for v in result)
    gain=min(.04/max(rms,1e-8),.6/max(peak,1e-8),20.)
    wav('mic_converted.wav',(v*gain for v in result))
    data=dict(native=stats,source_samples=len(source),source_rms=source_rms,source_peak=source_peak,
        source_fullscale_samples=sum(abs(v)>=32767/32768 for v in source),converted_raw_rms=rms,converted_raw_peak=peak,gain_only=gain,
        original_wav_sha256=sha('mic_original.wav'),converted_wav_sha256=sha('mic_converted.wav'),raw_converted_sha256=sha('mic_converted_raw.f32'),
        actual_board_inference=True,pc_inference_used=False,target_quality_accepted=False,continuous_real_time=False,capture_to_playback_latency_not_measured=True)
    writejson('microphone_board_trial.json',data);print(json.dumps(data),flush=True)
if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ['numerical','capture']:raise SystemExit('usage: run_board_checks.py numerical|capture')
    print(json.dumps(dict(stage=sys.argv[1],start_temperature_c=temperature())),flush=True)
    if sys.argv[1]=='numerical':numerical()
    else:capture()