import torch, torch.nn as nn
from transformers import HubertModel
hub=HubertModel.from_pretrained(r'D:\Tools_FPGA\workspace\voice_conversion_zynq7020\neural_reference\RVC\assets\hubert_base',local_files_only=True)
print('has feature_extractor:', hasattr(hub,'feature_extractor'))
w=torch.randn(1,32000)
fe=hub.feature_extractor(w)
print('fe shape', tuple(fe.shape), 'mean', fe.mean().item(), 'std', fe.std().item())
a=torch.randn(1,32000); b=torch.randn(1,32000)
mse=nn.functional.mse_loss(hub.feature_extractor(a),hub.feature_extractor(b))
print('random MSE', mse.item())
