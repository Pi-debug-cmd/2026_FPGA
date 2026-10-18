from pathlib import Path
import subprocess,json, numpy as np
p=Path(__file__).resolve().parent
rows=json.loads((p/'numerical_tests.json').read_text())['tests']
results=[]
for r in rows:
    name=r['name'];result=subprocess.run([str(p/'native_llvc_host.exe'),str(p/'llvc_step20.f32'),str(p/(name+'.input.f32')),str(p/(name+'.native.f32'))],capture_output=True,text=True,check=True)
    x=np.fromfile(p/(name+'.torch.f32'),dtype='<f4')
    y=np.fromfile(p/(name+'.native.f32'),dtype='<f4')
    assert len(x)==len(y)==r['samples'] and np.isfinite(y).all()
    error=y.astype(np.float64)-x
    nrmse=float(np.linalg.norm(error)/max(np.linalg.norm(x),1e-12))
    peak=float(np.max(np.abs(error))) if len(x) else 0
    results.append(dict(name=name,samples=len(x),normalized_rmse=nrmse,max_absolute_error=peak,native_stats=json.loads(result.stdout)))
    print(name,'NRMSE',nrmse,'MAX',peak,flush=True)
decision=dict(status='native_numerical_comparison',tests=results,reference='Exact unmodified LLVC step20 PyTorch stream',
              quality_accepted=False,real_time_verified=False,board_deployed=False)
(p/'native_numerical_verification.json').write_text(json.dumps(decision,indent=2),encoding='utf8')
# Migration agreement criterion, not a speech-quality or latency criterion.
assert all(r['normalized_rmse']<1e-3 and r['max_absolute_error']<1e-3 for r in results), 'native/PyTorch mismatch: inspect first-block intermediates'
print('NATIVE CONTRACT MATCH',flush=True)