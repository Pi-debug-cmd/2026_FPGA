import sys, torch
sys.path.insert(0, r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\neural_reference\LLVC")
from discriminators import MultiPeriodDiscriminatorV2
dev="cuda"
d=MultiPeriodDiscriminatorV2().to(dev)
print("disc params", sum(p.numel() for p in d.parameters()), flush=True)
# small input first
y=torch.randn(1,1,8000,device=dev); yhat=torch.randn(1,1,8000,device=dev)
yr,yg,fr,fg=d(y,yhat)
print("8000 ok", len(yr), flush=True)
# 2s
y=torch.randn(1,1,32000,device=dev); yhat=torch.randn(1,1,32000,device=dev)
yr,yg,fr,fg=d(y,yhat)
print("32000 ok", len(yr), flush=True)
