from run_rvc_pilot import settings
settings()
import torch, torch.nn as nn, numpy as np
torch.manual_seed(0)
# fresh random conv, same geometry
c = nn.Conv1d(1,512,48,stride=16,bias=False)
c1 = torch.ones(1,1,240)
with torch.inference_mode():
    y = c(c1).numpy().reshape(13,512)
W = c.weight.detach().numpy().reshape(512,48)
rowsum = W.sum(axis=1)
print("fresh random conv vs rowsum maxdiff:", np.abs(y[0]-rowsum).max())
print("conv frame0 first 5:", y[0,:5])
print("rowsum first 5:", rowsum[:5])
