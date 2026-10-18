from run_rvc_pilot import settings
settings()
import torch, torch.nn as nn
torch.manual_seed(0)
c = nn.Conv1d(1,8,48,stride=16,bias=False)   # small 8 output channels
c1 = torch.ones(1,1,240)
print("input all ones:", c1.unique().tolist())
with torch.inference_mode():
    y = c(c1)
print("output shape:", tuple(y.shape))
# torch indexing
for ch in range(8):
    print("ch",ch,"frame0 =", y[0,ch,0].item())
# weight row sums
W = c.weight.detach().reshape(8,48)
print("weight row sums:", W.sum(1).tolist())
