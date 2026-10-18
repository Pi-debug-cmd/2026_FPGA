from run_rvc_pilot import settings
settings()
from differentiable_fargan_20261006 import FrozenFargan,BASE
import torch,numpy as np,json,time
torch.set_num_threads(4);budget=BASE.parent/'board_budget_20261005';out=budget/'fargan_proxy_verification'
raw=np.fromfile(out/'features.f32',dtype='float32').reshape(-1,20);model=FrozenFargan().cuda().eval();x=torch.tensor(raw,device='cuda')[None]
with torch.no_grad():gold=model(x)
model.truncate_frames=8;x=x.requires_grad_(True);actual=model(x);loss=actual.square().mean();loss.backward()
report=dict(forward_max_abs=float((actual-gold).abs().max()),feature_gradient_max=float(x.grad.abs().max()),feature_gradient_finite=bool(torch.isfinite(x.grad).all()),truncation_frames=8,training_only=True,quality_accepted=False)
assert report['forward_max_abs']<1e-7 and report['feature_gradient_finite'] and report['feature_gradient_max']>0
(out/'truncated_gradient_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
