"""A bounded causal pitch correction of accepted neural outputs; not source mixing."""
from train_board_student_20261005 import BASE,read
from pathlib import Path
import numpy as np,json,subprocess,soundfile as sf,hashlib
native=BASE.parent/'board_support/native_llvc_20261005';budget=BASE.parent/'board_budget_20261005'
out=budget/'wide192_psola_post';out.mkdir(exist_ok=True)
parent=budget/'wide192_shallow2_target_anchor';doc=json.loads((parent/'decision.json').read_text(encoding='utf-8'))
outputs=[]
for row in doc['heldout_outputs']:
 x=read(row['student_path']);stem=Path(row['filename']).stem;inp=out/(stem+'.neural.f32');x.tofile(inp)
 dest=out/(stem+'.psola.f32');stats=out/(stem+'.psola.json')
 subprocess.run([str(native/'causal_psola_host.exe'),str(inp),str(dest),str(stats)],check=True,capture_output=True)
 y=np.fromfile(dest,dtype=np.float32);assert len(y)==len(x) and np.isfinite(y).all()
 path=out/(stem+'_student.wav');sf.write(path,y,16000,subtype='FLOAT')
 outputs.append(dict(row,student_path=str(path),parent_neural_path=row['student_path'],psola_stats=json.loads(stats.read_text()),human_acceptance=False))
 print('PSOLA',stem,outputs[-1]['psola_stats']['ratio'],flush=True)
(out/'decision.json').write_text(json.dumps(dict(complete=True,heldout_outputs=outputs,parent=str(parent),model_changed=False,causal_psola_postprocessing=True,algorithmic_extra_delay_ms=39,source_enrollment=False,unvoiced_path='same neural output with matched delay',original_audio_mixed_into_output=False,recognizer_used_as_loss=True,auxiliary_speaker_loss_used=True,quality_accepted=False,board_live_deployed=False),ensure_ascii=False,indent=2),encoding='utf-8')
contracts=[]
for name,hz,fixed in [('low',120,None),('high',270,None),('identity',120,1),('silence',0,None)]:
 x=(.1*np.sin(2*np.pi*hz*np.arange(48000)/16000)).astype('float32') if hz else np.zeros(48000,np.float32)
 inp=out/(name+'.input.f32');dest=out/(name+'.output.f32');stats=out/(name+'.status.json');x.tofile(inp)
 args=[str(native/'causal_psola_host.exe'),str(inp),str(dest),str(stats)]+([str(fixed)] if fixed else [])
 subprocess.run(args,check=True,capture_output=True);y=np.fromfile(dest,dtype=np.float32);assert len(y)==len(x) and np.isfinite(y).all()
 if name=='identity':assert np.array_equal(y,x)
 if hz:
  segment=y[-16000:];freq=float(np.fft.rfftfreq(len(segment),1/16000)[np.argmax(np.abs(np.fft.rfft(segment*np.hanning(len(segment)))))])
  expected=120 if fixed else 193.13304493;assert abs(freq-expected)<5,(name,freq)
 else:freq=0;assert np.max(np.abs(y))==0
 contracts.append(dict(name=name,input_hz=hz,output_hz=freq,samples=len(y),stats=json.loads(stats.read_text())))
(out/'contract.json').write_text(json.dumps(contracts,indent=2),encoding='utf-8')
print('PSOLA_SCREEN_DONE',flush=True)
