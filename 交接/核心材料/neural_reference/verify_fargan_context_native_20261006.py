from run_rvc_pilot import settings
settings()
from fargan_mapper_context_20261006 import MapperContext,context_features
from pathlib import Path
import numpy as np,torch,json,subprocess,soundfile as sf
base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';native=base.parent/'board_support/native_llvc_20261005'
folder=budget/'fargan_context_v9';out=folder/'native_verification';out.mkdir(exist_ok=True)
cp=torch.load(folder/'checkpoint_step10000.pt',map_location='cpu',weights_only=False)
model=MapperContext(cp['mean'],cp['std']);model.load_state_dict(cp['model']);model.eval();torch.set_num_threads(4)
weight=folder/'fargan_context_v9.f32';features=budget/'fargan_probe/fixed_B.features.f32';pcm=budget/'fargan_probe/fixed_B.input.pcm'
raw=np.fromfile(features,dtype='float32').reshape(-1,20)
with torch.inference_mode():gold,_=model(torch.tensor(context_features(raw))[None]);gold=gold[0].numpy()
mapped=out/'fixed_B.features.f32'
subprocess.run([str(native/'fargan_mapper_probe_context_host.exe'),str(weight),str(features),str(mapped),str(out/'mapper.json')],check=True)
actual=np.fromfile(mapped,dtype='float32').reshape(-1,20)
error=float(np.linalg.norm(actual-gold)/np.linalg.norm(gold));maximum=float(np.max(np.abs(actual-gold)))
assert error<1e-5 and maximum<1e-4
with pcm.open('rb') as i,(out/'fixed_B.pcm').open('wb') as o:
    subprocess.run([str(native/'native_fargan_context_host.exe'),str(weight),str(out/'pipeline.json')],stdin=i,stdout=o,check=True,timeout=30)
wave=np.fromfile(out/'fixed_B.pcm',dtype='<i2').astype('float32')/32768
assert len(wave)==69120 and np.isfinite(wave).all()
sf.write(out/'C_新训练转换_同一句中文.wav',wave,16000,subtype='FLOAT')
sf.write(out/'B_普通男声_同一句中文.wav',np.fromfile(native/'fixed_text_B_wide.input.f32',dtype='float32'),16000,subtype='FLOAT')
sf.write(out/'D_现有基线_同一句中文.wav',np.fromfile(native/'fixed_text_B_wide.torch.f32',dtype='float32'),16000,subtype='FLOAT')
quiet_input=out/'quiet.input.pcm';np.zeros(32000,dtype='<i2').tofile(quiet_input)
with quiet_input.open('rb') as i,(out/'quiet.output.pcm').open('wb') as o:
    subprocess.run([str(native/'native_fargan_context_host.exe'),str(weight),str(out/'quiet.json')],stdin=i,stdout=o,check=True,timeout=30)
quiet=np.fromfile(out/'quiet.output.pcm',dtype='<i2').astype('float64')/32768
report=dict(native_mapper_nrmse=error,native_mapper_max_abs=maximum,
            samples=len(wave),rms=float(np.sqrt(np.mean(wave**2))),peak=float(np.max(np.abs(wave))),
            clips=int(np.count_nonzero(np.abs(wave)>=32767/32768)),
            quiet_rms=float(np.sqrt(np.mean(quiet**2))),quiet_peak=float(np.max(np.abs(quiet))),
            quality_accepted=False,board_live_deployed=False,same_text='我的校园很美，走近大门就能看见宽阔的操场。',
            source_enrollment=False,raw_waveform_mix=False)
assert report['clips']==0 and report['quiet_rms']<.0002 and report['quiet_peak']<.001
(out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True),flush=True)
