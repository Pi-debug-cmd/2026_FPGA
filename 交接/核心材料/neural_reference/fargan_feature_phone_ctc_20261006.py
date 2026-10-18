"""Training-only acoustic phonetic sequence guide, all20 feature channels."""
from fargan_feature_phone_model_20261006 import FeaturePhoneNet
from torch import nn
import torch

class FeaturePhoneCTC(FeaturePhoneNet):
    def __init__(self,mean,std,classes):
        super().__init__(mean,std,classes);self.pre=nn.Linear(120,128)
    def forward(self,frames):
        n=frames.shape[1]//6
        x=((frames[:,:n*6]-self.mean)/self.std).reshape(frames.shape[0],n,120)
        h,_=self.gru(torch.tanh(self.pre(x)));return self.head(h)

def collapse(ids):
    result=[];previous=0
    for k in ids:
        if k and k!=previous:result.append(int(k))
        previous=k
    return result
