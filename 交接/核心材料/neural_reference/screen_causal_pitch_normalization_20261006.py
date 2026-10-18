"""Prototype automatic causal DSP then accepted neural student, no new training yet."""
from train_board_student_20261005 import BASE, read, stream
from prepare_wide_shallow_geometry import build_wide_shallow
from pathlib import Path
import torch,numpy as np,json,subprocess,soundfile as sf,hashlib
torch.set_num_threads(4)
native=BASE.parent/'board_support/native_llvc_20261005'
budget=BASE.parent/'board_budget_20261005'
out=budget/'wide192_causal_pitch_initial';out.mkdir(exist_ok=True)
parent=budget/'wide192_shallow2_target_anchor'
model,cfg,_=build_wide_shallow();model.load_state_dict(torch.load(parent/'checkpoint_step800.pt',map_location='cpu',weights_only=True)['model'],strict=True);model.eval()
decision=json.loads((parent/'decision.json').read_text(encoding='utf-8'))
outputs=[]
for row in decision['heldout_outputs']:
 x=read(row['path']);stem=Path(row['filename']).stem
 raw=out/(stem+'.source.f32');shift=out/(stem+'.pitch.f32');status=out/(stem+'.pitch.json');x.tofile(raw)
 subprocess.run([str(native/'causal_pitch_normalizer_host.exe'),str(raw),str(shift),str(status)],check=True,capture_output=True)
 pitched=np.fromfile(shift,dtype=np.float32);assert len(pitched)==len(x) and np.isfinite(pitched).all()
 pitchedwav=out/(stem+'_pitched_source.wav');sf.write(pitchedwav,pitched,16000,subtype='FLOAT')
 y=stream(model,pitched);path=out/(stem+'_student.wav');sf.write(path,y,16000,subtype='FLOAT')
 outputs.append(dict(row,student_path=str(path),pitch_source_path=str(pitchedwav),pitch_status=json.loads(status.read_text()),human_acceptance=False))
 print('NORMALIZED',stem,outputs[-1]['pitch_status']['source_median_hz'],outputs[-1]['pitch_status']['pitch_ratio'],flush=True)
report=dict(complete=True,heldout_outputs=outputs,config=cfg,parameters=sum(p.numel() for p in model.parameters()),model_changed=False,parent=str(parent),source_enrollment=False,causal_pitch_preprocessing=True,original_audio_mixed_into_output=False,target_pitch_hz=193.13304493,pitch_library_commit='f738b1132ec1fd56efc90367898244cf52d9e6a5',recognizer_used_as_loss=True,auxiliary_speaker_loss_used=True,human_quality_accepted=False,board_deployed=False)
(out/'decision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
# Algorithmic contract checks using causal block API, not speech quality tests.
contract=[]
for name,hz in [('low',120),('high',270),('silence',0)]:
 x=(.1*np.sin(2*np.pi*hz*np.arange(48000)/16000)).astype('float32') if hz else np.zeros(48000,np.float32)
 inp=out/(name+'.in.f32');dst=out/(name+'.out.f32');st=out/(name+'.json');x.tofile(inp)
 subprocess.run([str(native/'causal_pitch_normalizer_host.exe'),str(inp),str(dst),str(st)],check=True,capture_output=True)
 y=np.fromfile(dst,dtype=np.float32);assert len(y)==len(x) and np.isfinite(y).all()
 if hz:
  seg=y[-16000:];freq=np.fft.rfftfreq(len(seg),1/16000)[np.argmax(np.abs(np.fft.rfft(seg*np.hanning(len(seg)))))]
  assert abs(freq-193.13304493)<5,(name,freq)
 else:freq=0;assert np.max(np.abs(y))==0
 contract.append(dict(name=name,input_hz=hz,output_fft_hz=float(freq),samples=len(y),**json.loads(st.read_text())))
(out/'algorithm_contract.json').write_text(json.dumps(contract,indent=2),encoding='utf-8')
print('CAUSAL_PITCH_INITIAL_DONE',flush=True)
