"""Offline-only phonetic-body guidance. Never exported to7020."""
import torch
from torch import nn

class FeaturePhoneNet(nn.Module):
    def __init__(self,mean,std,classes):
        super().__init__();self.register_buffer('mean',torch.as_tensor(mean,dtype=torch.float32));self.register_buffer('std',torch.as_tensor(std,dtype=torch.float32))
        self.pre=nn.Linear(102,128);self.gru=nn.GRU(128,128,num_layers=2,bidirectional=True,batch_first=True,dropout=.1);self.head=nn.Linear(256,classes)
    def forward(self,frames):
        n=frames.shape[1]//6
        x=((frames[:,:n*6,1:18]-self.mean)/self.std).reshape(frames.shape[0],n,102)
        h,_=self.gru(torch.tanh(self.pre(x)));return self.head(h)

def posterior_loss(logits,truth,mask):
    # Confidence weighting for sparse CTC peaks, rather than counting silence
    # as successful syllable recognition. Probabilities are teacher diagnostics.
    weight=mask*(.15+3*(1-truth[...,0]))
    ce=-(truth*logits.log_softmax(-1)).sum(-1)
    return (ce*weight).sum()/weight.sum().clamp_min(1)
