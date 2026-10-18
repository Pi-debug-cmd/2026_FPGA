"""Audit trained students' bulk vs deployed stream, without microphone capture."""
from train_board_student_20261005 import BASE,build_small,stream,read
from pathlib import Path
import json,torch,numpy as np,tarfile,hashlib
torch.set_num_threads(4)
native=BASE.parent/'board_support/native_llvc_20261005'
budget=BASE.parent/'board_budget_20261005'
archive=native/'small128_vmath_results.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='5bad6414622f2e21bf26fad2efcd1e5b5b8bbcd5181ac9b74f652ba293b79f42'
folder=native/'small128_vmath_results';folder.mkdir(exist_ok=True)
with tarfile.open(archive) as tar:tar.extractall(folder,filter='data')
checks=[]
for name in ['real_16000','tone_1000','fleurs_full']:
 a=np.fromfile(folder/(name+'.small128_vmath.arm.f32'),dtype='<f4')
 b=np.fromfile(native/(name+'.small128_initial.torch.f32'),dtype='<f4')
 assert len(a)==len(b) and np.isfinite(a).all()
 row=dict(case=name,samples=len(a),normalized_rmse=float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-12)),maximum_absolute_error=float(np.max(np.abs(a-b))))
 assert row['normalized_rmse']<.0001,row
 checks.append(row)
perf=[json.loads((folder/('bench_small128_vmath_'+n+'.json')).read_text()) for n in ['real','fleurs','tone']]
(native/'small128_vmath_board_check.json').write_text(json.dumps(dict(numerical_checks=checks,board_benchmarks=perf,trained=False,quality_accepted=False,live_acoustic_latency_verified=False,original_audio_unchanged=True),indent=2))
print('ARM_PARITY',json.dumps(checks),flush=True)
rows=json.loads((budget/'student_corpus/paired_manifest.json').read_text(encoding='utf-8'))['files']
source=next(r for r in rows if r['split']=='validation');x=read(source['path'])[:48000]
reports=[]
for name,enc,path in [('96initial',96,None),('96step6400',96,budget/'small96_identity_training/checkpoint_step4000.pt'),('96step9200',96,budget/'small96_noise_refinement/checkpoint_step1200.pt'),('96phonetic',96,budget/'small96_phonetic_pilot/checkpoint_step400.pt'),('128initial',128,None)]:
 model,cfg,_=build_small(enc)
 if path:model.load_state_dict(torch.load(path,map_location='cpu',weights_only=True)['model'],strict=True)
 with torch.inference_mode():bulk=model(torch.tensor(x)[None,None]).numpy().reshape(-1)
 online=stream(model,x)
 a,b=bulk[8192:],online[8192:]
 report=dict(name=name,source=source['path'],checkpoint=str(path),normalized_rmse=float(np.linalg.norm(a-b)/max(np.linalg.norm(a),1e-12)),max_abs=float(np.max(np.abs(a-b))),bulk_rms=float(np.sqrt(np.mean(a*a))),stream_rms=float(np.sqrt(np.mean(b*b))))
 reports.append(report);print('BULK_STREAM',json.dumps(report),flush=True)
(native/'updated_student_bulk_stream_audit.json').write_text(json.dumps(dict(comparisons=reports,scope='single existing public validation source, not quality approval'),indent=2))
