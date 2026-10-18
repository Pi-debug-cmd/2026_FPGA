from run_rvc_pilot import settings
settings()
import torch, torch.nn as nn
torch.manual_seed(0)
c = nn.Conv1d(1,512,48,stride=16,bias=False)
c1 = torch.ones(1,1,240)
with torch.inference_mode():
    y = c(c1)
print("output shape:", tuple(y.shape))
for ch in [0,1,2,3,4,100,511]:
    print("ch",ch,"frame0 =", y[0,ch,0].item())
W = c.weight.detach().reshape(512,48).sum(1)
print("weight rowsum ch0..4:", [round(W[ch].item(),4) for ch in range(5)])
