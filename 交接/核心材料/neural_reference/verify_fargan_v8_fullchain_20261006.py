from run_rvc_pilot import settings
settings()
from fargan_mapper_v8_20261006 import MapperV8,pitch_aware_features
from pathlib import Path
import numpy as np,torch,json,subprocess,soundfile as sf
base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';native=base.parent/'board_support/native_llvc_20261005';trained=budget/'fargan_mapper_expanded_v8';out=budget/'fargan_v8_fullchain_verification';out.mkdir(exist_ok=True)
cp=torch.load(trained/'checkpoint_step5000.pt',map_location='cpu',weights_only=False);model=MapperV8(cp['mean'],cp['std']);model.load_state_dict(cp['model']);model.eval();torch.set_num_threads(4)
weight=trained/'fargan_mapper_expanded_v8.f32';inputpcm=budget/'fargan_probe/fixed_B.input.pcm';inputfeat=budget/'fargan_probe/fixed_B.features.f32';raw=np.fromfile(inputfeat,dtype='float32').reshape(-1,20)
with torch.inference_mode():gold,_=model(torch.tensor(pitch_aware_features(raw))[None]);gold=gold[0].numpy()
mapped=out/'features.f32';subprocess.run([str(native/'fargan_mapper_probe_v8_host.exe'),str(weight),str(inputfeat),str(mapped),str(out/'map.json')],check=True)
actual=np.fromfile(mapped,dtype='float32').reshape(-1,20);nrmse=float(np.linalg.norm(actual-gold)/np.linalg.norm(gold));maxabs=float(np.max(np.abs(actual-gold)));assert nrmse<1e-5 and maxabs<1e-4
subprocess.run([str(native/'fargan_probe_host.exe'),'--synthesis',str(mapped),str(out/'file.pcm'),str(out/'file.json')],check=True)
with inputpcm.open('rb') as f,(out/'pipeline.pcm').open('wb') as o:subprocess.run([str(native/'native_fargan_v8_host.exe'),str(weight),str(out/'pipeline.json')],stdin=f,stdout=o,check=True,timeout=30)
assert (out/'file.pcm').read_bytes()==(out/'pipeline.pcm').read_bytes()
wave=np.fromfile(out/'pipeline.pcm',dtype='<i2').astype('float32')/32768;assert len(wave)==69120 and np.isfinite(wave).all();sf.write(out/'C_新版转换_同一句中文.wav',wave,16000,subtype='FLOAT')
source=np.fromfile(native/'fixed_text_B_wide.input.f32',dtype='float32');old=np.fromfile(native/'fixed_text_B_wide.torch.f32',dtype='float32');sf.write(out/'B_普通男声_同一句中文.wav',source,16000,subtype='FLOAT');sf.write(out/'D_现有基线_同一句中文.wav',old,16000,subtype='FLOAT')
zeros=out/'zero_input.pcm';np.zeros(32000,dtype='<i2').tofile(zeros)
with zeros.open('rb') as f,(out/'zero_output.pcm').open('wb') as o:subprocess.run([str(native/'native_fargan_v8_host.exe'),str(weight),str(out/'zero.json')],stdin=f,stdout=o,check=True,timeout=30)
quiet=np.fromfile(out/'zero_output.pcm',dtype='<i2').astype('float64')/32768
report=dict(complete=True,native_mapper_nrmse=nrmse,native_mapper_max_abs=maxabs,threaded_pipeline_file_chain_bit_exact=True,samples=len(wave),rms=float(np.sqrt(np.mean(wave**2))),peak=float(np.max(np.abs(wave))),clip_count=int(np.count_nonzero(np.abs(wave)>=32767/32768)),quiet_rms=float(np.sqrt(np.mean(quiet**2))),quiet_peak=float(np.max(np.abs(quiet))),pipeline_stats=json.loads((out/'pipeline.json').read_text()),same_text='我的校园很美，走近大门就能看见宽阔的操场。',source_enrollment=False,raw_waveform_mix=False,quality_accepted=False,board_live_deployed=False)
assert report['clip_count']==0 and report['quiet_rms']<.0002 and report['quiet_peak']<.001
(out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=True),flush=True)
