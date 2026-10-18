import sys, torch, auraloss
sys.path.insert(0, r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\neural_reference\LLVC")
sys.path.insert(0, r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\neural_reference")
from load_llvc_audit_model import load_model
from transformers import HubertModel
from discriminators import MultiPeriodDiscriminatorV2, generator_loss, feature_loss
dev="cuda"
net,cfg=load_model(False)
import torch
sd=torch.load(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\neural_reference\llvc_pretrained_audit\G_500000.pth",map_location="cpu",weights_only=True)["model"]
net.load_state_dict(sd,strict=True); net=net.to(dev).train()
disc=MultiPeriodDiscriminatorV2().to(dev).train()
hub=HubertModel.from_pretrained(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\neural_reference\RVC\assets\hubert_base",local_files_only=True).to(dev).eval()
for p in hub.parameters(): p.requires_grad_(False)
mr=auraloss.freq.MultiResolutionSTFTLoss(scale="mel",sample_rate=16000,device=dev,fft_sizes=[1024,2048,512],hop_sizes=[120,240,50],win_lengths=[600,1200,240],n_bins=80).to(dev)
N=32000
src=torch.randn(1,N,device=dev); tch=torch.randn(1,N,device=dev)
print("mem before", torch.cuda.memory_allocated()//1024//1024, flush=True)
pred=net(src[:,None])[:,0].float()
yr,yg,fr,fg=disc(tch[:,None],pred[:,None])
gl=generator_loss(yg)[0]; fm=feature_loss(fr,fg)
import torch.nn.functional as F
content=F.mse_loss(hub.feature_extractor(pred),hub.feature_extractor(tch))
mel=mr(pred[:,None],tch[:,None])
loss=100000*content+10*mel+gl+2*fm
print("mem graph", torch.cuda.memory_allocated()//1024//1024, flush=True)
loss.backward()
print("backward ok N=16000", flush=True)
