from pathlib import Path
import subprocess,json,numpy as np,hashlib
p=Path(__file__).resolve().parent
cases=json.loads((p/'numerical_tests.json').read_text())['tests'];rows=[]
for c in cases:
    n=c['name'];r=subprocess.run([str(p/'native_llvc_neon_order_host.exe'),str(p/'llvc_step20.f32'),str(p/(n+'.input.f32')),str(p/(n+'.neon_order.f32'))],capture_output=True,text=True,check=True)
    a=np.fromfile(p/(n+'.torch.f32'),dtype='<f4');b=np.fromfile(p/(n+'.neon_order.f32'),dtype='<f4')
    nrmse=float(np.linalg.norm(a.astype(np.float64)-b)/max(np.linalg.norm(a),1e-12))
    peak=float(np.max(np.abs(a-b)))
    rows.append(dict(name=n,normalized_rmse=nrmse,max_absolute_error=peak));assert nrmse<1e-3 and peak<1e-3
# Explicitly exercise zero/short/invalid finite-input contracts.
for size in [0,1,16,207,208,224,416]:
    name='length_'+str(size);a=np.zeros(size,dtype='<f4');a.tofile(p/(name+'.input.f32'))
    r=subprocess.run([str(p/'native_llvc_host.exe'),str(p/'llvc_step20.f32'),str(p/(name+'.input.f32')),str(p/(name+'.native.f32'))],capture_output=True,text=True,check=True)
    assert (p/(name+'.native.f32')).stat().st_size==4*size
np.array([np.nan],dtype='<f4').tofile(p/'invalid_nan.input.f32')
r=subprocess.run([str(p/'native_llvc_host.exe'),str(p/'llvc_step20.f32'),str(p/'invalid_nan.input.f32'),str(p/'invalid_nan.native.f32')],capture_output=True,text=True)
assert r.returncode!=0
data=dict(neon_accumulation_order_emulated=True,not_executed_on_arm_yet=True,tests=rows,empty_short_eof_lengths_passed=[0,1,16,207,208,224,416],nonfinite_input_rejected=True,board_deployed=False,real_time_verified=False)
(p/'native_neon_order_verification.json').write_text(json.dumps(data,indent=2),encoding='utf8')
artifacts=[]
for name in ['native_llvc.cpp','export_model.py','verify_native.py','native_llvc_arm','llvc_step20.f32']:
    f=p/name;artifacts.append(dict(path=str(f),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
(p/'deployment_artifacts.json').write_text(json.dumps(dict(status='ARM binary prepared, board shell unavailable; actual execution NOT verified',artifacts=artifacts),ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(neon_order_tests=rows,artifacts=artifacts),ensure_ascii=True,indent=2))