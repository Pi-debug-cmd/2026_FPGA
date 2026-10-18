from pathlib import Path
import subprocess,json,struct,math,tarfile,gzip,hashlib
r=Path(__file__).resolve().parent
old=r/'native_llvc_small96_stream_host.exe'
new=r/'native_llvc_small96_meter_host.exe'
model=r/'small96_initial.f32'
pcm=(r/'fleurs_full.s16').read_bytes()[:32000]
cases=[]
for n in [0,224,16000]:
    x=pcm[:2*n]
    a=subprocess.run([str(old),'--stream',str(model)],input=x,capture_output=True,check=True)
    b=subprocess.run([str(new),'--stream',str(model)],input=x,capture_output=True,check=True)
    assert a.stdout==b.stdout and len(b.stdout)==2*n
    z=json.loads(b.stderr)
    assert z['input_gain']==1 and z['output_gain']==1
    assert 'meter_window_input' in z
    if n==224:
        xs=struct.unpack('<224h',x)
        assert abs(z['meter_window_input']['rms']-math.sqrt(sum((v/32768)**2 for v in xs)/224))<1e-6
        assert z['meter_window_input']['samples']==224
    cases.append({'samples':n,'identical_to_original_stream':True})
report={'default_gain_pcm_parity':cases,'input_meter_rms_checked':True,'microphone_audio_saved':False}
(r/'meter_adapter_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
with tarfile.open(r/'meter_runtime_bundle.tar.gz','w:gz') as t:
    t.add(r/'native_llvc_small96_meter_arm',arcname='native_llvc_small96_meter_arm')
print(json.dumps(report))
print('bundle bytes:',(r/'meter_runtime_bundle.tar.gz').stat().st_size)
