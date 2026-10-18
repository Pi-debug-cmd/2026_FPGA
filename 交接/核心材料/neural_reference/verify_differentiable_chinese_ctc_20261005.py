from pathlib import Path
import json,time
import numpy as np,torch,onnxruntime as ort
from run_rvc_pilot import settings
settings()
from differentiable_chinese_ctc_20261005 import FrozenChineseCTC,MODEL
from run_sensevoice_pinyin_validation_20261004 import load_frontend
BASE=Path(__file__).resolve().parent;OUT=BASE.parent/'board_support/native_llvc_20261005';torch.set_num_threads(4)
torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
opts=ort.SessionOptions();opts.intra_op_num_threads=4;session=ort.InferenceSession(str(MODEL),sess_options=opts,providers=['CPUExecutionProvider'])
model=FrozenChineseCTC().eval();front=load_frontend();reports=[]
for seed,batch,T in [(20261005,1,16),(20261006,2,24)]:
 torch.manual_seed(seed);f=torch.randn(batch,T,560);lengths=torch.tensor([T-i*3 for i in range(batch)],dtype=torch.int32)
 ref=session.run(None,dict(feats=f.numpy(),feats_lens=lengths.numpy()))
 begin=time.monotonic()
 with torch.no_grad():out=model(f,lengths)
 row={'batch':batch,'T':T,'cpu_seconds':time.monotonic()-begin,'outputs':[]}
 for k,a,b in zip(session.get_outputs(),ref,out):
  b=b.numpy();assert a.shape==b.shape,(a.shape,b.shape);err=float(np.max(np.abs(a.astype('float64')-b)));assert err<.003,(k.name,err)
  row['outputs'].append({'name':k.name,'max_absolute_error':err})
 reports.append(row);print('PARITY',json.dumps(row),flush=True)
wave=np.fromfile(OUT/'fleurs_full.input.f32',dtype='<f4')[:32000];wave=wave/max(float(np.max(np.abs(wave))),1e-8);x=torch.tensor(wave)[None].requires_grad_();f,l=front(x,torch.tensor([len(wave)]));ref=session.run(None,dict(feats=f.detach().numpy().astype('float32'),feats_lens=l.numpy().astype('int32')))
with torch.no_grad():out=model(f,l)
errors=[float(np.max(np.abs(a-b.numpy()))) for a,b in zip(ref,out)];assert max(errors)<.003;print('WAVE_PARITY',errors,flush=True)
del session;model=model.cuda();front=front.cuda();x=torch.tensor(wave,device='cuda')[None].requires_grad_();begin=time.monotonic();f,l=front(x,torch.tensor([len(wave)]));h,p,n=model(f,l)
loss=-p[4:10,0,1:4].mean();loss.backward();assert x.grad is not None and torch.isfinite(x.grad).all() and float(x.grad.abs().max())>0
report={'cpu_parity':reports,'wave_parity_errors':errors,'model_sha256':model.model_sha256,'waveform_gradient_finite':True,'waveform_gradient_rms':float(x.grad.square().mean().sqrt()),'cuda_forward_backward_seconds':time.monotonic()-begin,'cuda_max_allocated':torch.cuda.max_memory_allocated(),'recognizer_frozen_buffers_only':len(list(model.parameters()))==0,'use_scope':'Offline loss only; loses independent-evaluator status after training use; not a7020 component'}
(OUT/'differentiable_chinese_ctc_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2),flush=True)
