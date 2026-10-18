from pathlib import Path
import subprocess,os,json,tarfile
r=Path(__file__).resolve().parent
model=r.parents[1]/'board_budget_20261005/small96_noise_refinement/small96_noise_step9200.f32'
old=r/'native_llvc_small96_meter_host.exe';new=r/'native_llvc_small96_diag120_host.exe'
base=(r/'fleurs_full.s16').read_bytes();pcm=(base*20)[:(208*9330+16)*2]
env=os.environ.copy();flag=r/'diagnostic120_test.trigger';prefix=r/'diagnostic120_host_test'
env['LLVC_DIAG_TRIGGER']=str(flag);env['LLVC_DIAG_PREFIX']=str(prefix)
flag.unlink(missing_ok=True)
for n in [0,224,16000]:
    a=subprocess.run([str(old),'--stream',str(model)],input=pcm[:n*2],capture_output=True,check=True)
    b=subprocess.run([str(new),'--stream',str(model)],input=pcm[:n*2],capture_output=True,env=env,check=True)
    assert a.stdout==b.stdout and len(b.stdout)==n*2
p=subprocess.Popen([str(new),'--stream',str(model)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
produced=bytearray();p.stdin.write(pcm[:448]);p.stdin.flush();produced.extend(p.stdout.read(416));at=448
for i in range(1,9330):
    if i==9250:flag.write_text('capture paired diagnostic after test')
    p.stdin.write(pcm[at:at+416]);p.stdin.flush();at+=416;produced.extend(p.stdout.read(416))
p.stdin.close();produced.extend(p.stdout.read());stderr=p.stderr.read();assert p.wait(timeout=10)==0
meta=json.loads((Path(str(prefix)+'.json')).read_text());start=meta['start_sample']*2;end=meta['end_sample']*2
assert meta['samples']==208*9231 and meta['start_sample']>0
assert Path(str(prefix)+'.input.s16').read_bytes()==pcm[start:end]
assert Path(str(prefix)+'.output.s16').read_bytes()==bytes(produced[start:end])
report={'default_pcm_matches_prior':True,'wraparound_input_output_alignment_exact':True,'samples_retained':meta['samples'],'diagnostic_dump_after_requested_flag':True,'user_audio_used':False}
(r/'diagnostic120_ring_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

env['LLVC_DIAG_SILENT_PLAYBACK']='1'
flag.write_text('explicit synthetic silence-path test')
a=subprocess.run([str(old),'--stream',str(model)],input=pcm[:32000],capture_output=True,check=True)
b=subprocess.run([str(new),'--stream',str(model)],input=pcm[:32000],capture_output=True,env=env,check=True)
assert b.stdout==bytes(32000)
assert Path(str(prefix)+'.input.s16').read_bytes()==pcm[:32000]
assert Path(str(prefix)+'.output.s16').read_bytes()==a.stdout
report['silent_speaker_does_not_change_stored_model_output']=True
(r/'diagnostic120_ring_verification.json').write_text(json.dumps(report,indent=2))
with tarfile.open(r/'diagnostic120_bundle.tar.gz','w:gz') as t:
    for name in ['native_llvc_small96_diag120_arm','board_neural_diag120.sh']:t.add(r/name,arcname=name)
print(json.dumps(report));print('bundle bytes:',(r/'diagnostic120_bundle.tar.gz').stat().st_size)
