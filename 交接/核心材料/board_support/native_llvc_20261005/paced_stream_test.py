#!/usr/bin/env python3
"""Existing public PCM arrives in13ms packets; never captures user speech."""
import subprocess,os,time,json,threading
ROOT='/home/root/native_llvc_trial_20261005/'
data=open(ROOT+'fleurs_full.s16','rb').read()
first_event=threading.Event();results={'output_bytes':0}
begin=time.monotonic()
p=subprocess.Popen([ROOT+'native_llvc_small96_stream_arm','--stream',ROOT+'small96_initial.f32',ROOT+'paced_stream_status.json'],
    stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=open(ROOT+'paced_stream.error','wb'),bufsize=0)
def drain():
    while True:
        block=p.stdout.read(416)
        if not block:break
        if not first_event.is_set():results['first_output_seconds']=time.monotonic()-begin;first_event.set()
        results['output_bytes']+=len(block)
t=threading.Thread(target=drain);t.start()
# Load/setup may backpressure the first packet; start cadence only after the
# first block has arrived, then measure sustained processing.
p.stdin.write(data[:448])
if not first_event.wait(10):raise RuntimeError('no first bounded block')
cadence=time.monotonic();max_write=0
for i,offset in enumerate(range(448,len(data),416)):
    deadline=cadence+(i+1)*.013
    wait=deadline-time.monotonic()
    if wait>0:time.sleep(wait)
    start=time.monotonic();p.stdin.write(data[offset:offset+416]);max_write=max(max_write,time.monotonic()-start)
p.stdin.close()
code=p.wait(timeout=15);t.join(timeout=5)
assert code==0 and not t.is_alive() and results['output_bytes']==len(data)
stats=json.load(open(ROOT+'paced_stream_status.json'))
results.update(stats,actual_board_execution=True,source='Previously frozen public FLEURS PCM; not microphone',
    received_bytes=len(data),wall_seconds=time.monotonic()-begin,max_producer_write_seconds=max_write,
    audio_seconds=len(data)/32000,input_packet_samples=208,input_cadence_ms=13,
    actual_alsa_duplex_verified=False,acoustic_latency_measured=False,target_quality_accepted=False)
with open(ROOT+'paced_stream_result.json','w') as f:json.dump(results,f,indent=2)
print(json.dumps(results),flush=True)
