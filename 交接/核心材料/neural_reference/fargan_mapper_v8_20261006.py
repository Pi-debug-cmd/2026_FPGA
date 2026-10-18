"""Larger causal mapper: native-budget128x2 GRU, target pitch from frame one."""
from fargan_feature_mapper_20261006 import pitch_aware_features,TARGET_PITCH_COORD
import torch
from torch import nn
class MapperV8(nn.Module):
    format_version=8
    def __init__(self,mean,std):
        super().__init__();self.register_buffer('mean',torch.tensor(mean,dtype=torch.float32));self.register_buffer('std',torch.tensor(std,dtype=torch.float32))
        self.pre=nn.Linear(21,128);self.gru=nn.GRU(128,128,num_layers=2,batch_first=True);self.head=nn.Linear(128,19)
        nn.init.zeros_(self.head.weight);nn.init.zeros_(self.head.bias)
    def forward(self,x,state=None):
        h,state=self.gru(torch.tanh(self.pre((x-self.mean)/self.std)),state);d=self.head(h);y=x[...,:20].clone()
        y[...,1:18]=x[...,1:18]+self.std[1:18]*3*torch.tanh(d[...,:17]/3)
        y[...,18]=(TARGET_PITCH_COORD+1.2*torch.tanh(d[...,17])).clamp(-1.49,1.5)
        y[...,19]=(x[...,19]+.5*torch.tanh(d[...,18])).clamp(-.5,.5)
        return y,state
class ConditionalFeatureDisc(nn.Module):
    def __init__(self):
        super().__init__();self.layers=nn.ModuleList([nn.Conv1d(39,64,5,2,2),nn.Conv1d(64,128,5,2,2),nn.Conv1d(128,128,5,2,2)]);self.out=nn.Conv1d(128,1,1)
    def forward(self,condition,output):
        h=torch.cat([condition,output],-1).transpose(1,2);maps=[]
        for layer in self.layers:h=torch.nn.functional.leaky_relu(layer(h),.1);maps.append(h)
        return self.out(h),maps
