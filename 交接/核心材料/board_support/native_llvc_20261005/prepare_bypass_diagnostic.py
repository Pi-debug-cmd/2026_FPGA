from pathlib import Path
import subprocess,json,tarfile,struct,math
r=Path(__file__).resolve().parent
pcm=(r/'fleurs_full.s16').read_bytes()[:32000]
rows=[]
for n in [0,1,207,208,224,16000]:
    stat=r/'bypass_host_status.json'
    z=subprocess.run([str(r/'pcm_bridge_bypass_host.exe'),str(stat)],input=pcm[:n*2],capture_output=True,check=True)
    assert z.stdout==pcm[:n*2]
    s=json.loads(stat.read_text());assert s['input_samples']==n and s['output_samples']==n
    rows.append({'samples':n,'identical_pcm':True})
p=subprocess.Popen([str(r/'pcm_bridge_bypass_host.exe'),str(r/'bypass_host_status.json')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
p.stdin.write(pcm[:416]);p.stdin.flush();assert p.stdout.read(416)==pcm[:416]
p.stdin.close();assert p.stdout.read()==b'';assert p.wait(timeout=5)==0
(r/'bypass_verification.json').write_text(json.dumps({'cases':rows,'first_chunk_before_eof':True,'diagnostic_only':True},indent=2))
s=(r/'board_neural_meter.sh').read_text(encoding='utf-8')
s=s.replace('native_llvc_small96_meter_arm','pcm_bridge_bypass_arm')
s=s.replace('"$DIR/pcm_bridge_bypass_arm" --stream "$DIR/small96_step6400.f32" "$RUN/status.json"','"$DIR/pcm_bridge_bypass_arm" "$RUN/status.json"')
s=s.replace('NEURAL_LIVE_START_REQUESTED','ORIGINAL_PASSTHROUGH_DIAGNOSTIC_STARTED_NOT_CONVERSION')
(r/'board_bridge_bypass.sh').write_text(s,encoding='utf-8')
with tarfile.open(r/'bypass_diagnostic_bundle.tar.gz','w:gz') as t:
    for name in ['pcm_bridge_bypass_arm','board_bridge_bypass.sh']:
        t.add(r/name,arcname=name)
print('PCM parity and first chunk tests passed. Bundle bytes:',(r/'bypass_diagnostic_bundle.tar.gz').stat().st_size)
