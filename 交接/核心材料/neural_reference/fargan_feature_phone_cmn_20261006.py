"""Offline helper with per-segment channel mean compensation.
Uses whole supplied segment ONLY in this non-deployed guidance model.
"""
from fargan_feature_phone_ctc_20261006 import FeaturePhoneCTC,collapse
import torch
class FeaturePhoneCMN(FeaturePhoneCTC):
    def forward(self,frames):
        n=frames.shape[1]//6;frames=frames[:,:n*6]
        x=(frames-self.mean)/self.std
        mask=(frames[...,0]>-7).to(frames.dtype)[...,None]
        mean=(x[...,1:19]*mask).sum(1,keepdim=True)/mask.sum(1,keepdim=True).clamp_min(1)
        x=torch.cat([x[...,:1],x[...,1:19]-mean,x[...,19:]],-1).reshape(frames.shape[0],n,120)
        h,_=self.gru(torch.tanh(self.pre(x)));return self.head(h)
