"""Synthetic/public-input diagnosis only; no user waveform recorded."""
from pathlib import Path
import subprocess,json,hashlib,argparse
import numpy as np
r=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--model');parser.add_argument('--outstem',default='low_level');args=parser.parse_args()
assert args.outstem.replace('_','').isalnum()
model=Path(args.model) if args.model else r.parents[1]/'board_budget_20261005/small96_identity_training/small96_trained.f32'
if not args.model:assert hashlib.sha256(model.read_bytes()).hexdigest()=='dbe07ea6d3f9dba5d81e8fdd44fa84b0426966fe67f684546e91946a97681ce8'
out=r/(args.outstem+'_diagnosis');out.mkdir(exist_ok=True)
n=32000;t=np.arange(n)/16000
source=np.fromfile(r/'fleurs_full.input.f32',dtype='<f4')[:n]
rng=np.random.default_rng(20261005)
signals={'zero':np.zeros(n),'dc_0.001':np.full(n,.001),'hum50_rms0.001':np.sin(2*np.pi*50*t)*.001*np.sqrt(2),
 'noise_rms0.001':rng.normal(0,.001,n),'noise_rms0.002':rng.normal(0,.002,n),'noise_rms0.004':rng.normal(0,.004,n),
 'public_speech_rms0.002':source*(.002/np.sqrt(np.mean(source**2))),
 'public_speech_rms0.04':source*(.04/np.sqrt(np.mean(source**2)))}
rows=[]
for name,x in signals.items():
    x=x.astype('<f4');inp=out/(name+'.input.f32');yp=out/(name+'.output.f32');x.tofile(inp)
    z=subprocess.run([str(r/'native_llvc_small96_meter_host.exe'),str(model),str(inp),str(yp)],capture_output=True,check=True)
    y=np.fromfile(yp,dtype='<f4');assert len(y)==len(x) and np.isfinite(y).all()
    tail=y[16000:].astype('float64');center=tail-tail.mean();fft=np.fft.rfft(center*np.hanning(len(center)));freq=np.fft.rfftfreq(len(center),1/16000);power=np.abs(fft)**2
    rows.append({'case':name,'input_rms':float(np.sqrt(np.mean(x*x))), 'output_rms':float(np.sqrt(np.mean(y*y))),
      'steady_output_rms':float(np.sqrt(np.mean(tail*tail))),'steady_output_dc':float(tail.mean()),
      'output_peak':float(np.max(np.abs(y))),'output_energy_below_200hz_fraction':float(power[freq<200].sum()/max(power.sum(),1e-30)),
      'steady_strongest_non_dc_frequency_hz':float(freq[np.argmax(power)]),'host_diagnostic_not_acoustic_board_test':True})
report={'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'cases':rows,'human_audio_saved':False,'naturalness_not_accepted':True}
(r/(args.outstem+'_robustness.json')).write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
