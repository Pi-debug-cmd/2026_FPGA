"""Causal20-feature conversion: no ASR, source enrollment or waveform bypass."""
import numpy as np
import torch
from torch import nn
TARGET_F0_CENTER=193.13304493
TARGET_PITCH_COORD=float(np.log2(TARGET_F0_CENTER/62.5)-1.5)

def normalize_pitch(features):
    result=features.copy();values=[];next_slot=0;quiet=0;correction=0.
    for i,row in enumerate(features):
        if row[19]>.1 and row[0]>-7:
            quiet=0
            if len(values)<151:values.append(float(row[18]))
            else:values[next_slot]=float(row[18]);next_slot=(next_slot+1)%151
        elif row[19]<-.2 or row[0]<-9:
            quiet+=1
            if quiet>80:values=[];next_slot=0
        desired=float(np.clip(TARGET_PITCH_COORD-np.median(values),np.log2(.65),np.log2(2.2))) if len(values)>=8 else 0.
        correction+=.055*(desired-correction)
        result[i,18]=np.clip(row[18]+correction,-1.49,1.5)
    return result

def normalize_spectrum(features,reference):
    """Past-only cepstral channel/voice normalization; adaptation is not enrollment."""
    result=normalize_pitch(features);history=[];next_slot=0;correction=np.zeros(17,dtype=np.float64)
    for i,row in enumerate(features):
        if row[0]>-7:
            if len(history)<200:history.append(row[1:18].astype('float64'))
            else:history[next_slot]=row[1:18].astype('float64');next_slot=(next_slot+1)%200
        desired=np.clip(reference-np.mean(history,axis=0),-4,4) if len(history)>=32 else np.zeros(17)
        correction+=.08*(desired-correction);result[i,1:18]=row[1:18]+correction
    return result

class FeatureMapper(nn.Module):
    def __init__(self,mean,std):
        super().__init__();self.register_buffer('mean',torch.tensor(mean,dtype=torch.float32));self.register_buffer('std',torch.tensor(std,dtype=torch.float32))
        self.pre=nn.Linear(20,64);self.gru=nn.GRU(64,64,batch_first=True);self.head=nn.Linear(64,18)
        nn.init.zeros_(self.head.weight);nn.init.zeros_(self.head.bias)
    def forward(self,x,state=None):
        z=torch.tanh(self.pre((x-self.mean)/self.std));h,state=self.gru(z,state);delta=self.head(h)
        y=x.clone();y[...,1:18]=x[...,1:18]+self.std[1:18]*3*torch.tanh(delta[...,:17]/3)
        y[...,18]=(x[...,18]+.4*torch.tanh(delta[...,17])).clamp(-1.49,1.5)
        # Energy and periodicity are kept from this input feature stream.
        return y,state

def pitch_aware_features(features):
    # The network must see both requested output pitch AND source pitch.
    # Normalizing in-place previously discarded a useful source-voice cue.
    return np.concatenate([normalize_pitch(features),features[:,18:19]],axis=1)

class PitchAwareMapper(FeatureMapper):
    def __init__(self,mean,std):
        super().__init__(mean,std);self.pre=nn.Linear(21,64)
    def forward(self,x,state=None):
        z=torch.tanh(self.pre((x-self.mean)/self.std));h,state=self.gru(z,state);delta=self.head(h)
        y=x[...,:20].clone();y[...,1:18]=x[...,1:18]+self.std[1:18]*3*torch.tanh(delta[...,:17]/3)
        y[...,18]=(x[...,18]+.4*torch.tanh(delta[...,17])).clamp(-1.49,1.5)
        return y,state

def export_mapper(model,path):
    import struct,json
    state=model.state_dict();meta=[]
    with open(path,'wb') as f:
        version=getattr(model,'format_version',0)
        magic=b'FMAP009\0' if version==9 else (b'FMAP008\0' if version==8 else (b'FMAP007\0' if model.mean.numel()==21 else b'FMAP006\0'))
        f.write(magic);f.write(struct.pack('<I',len(state)))
        for name,v in state.items():
            a=v.detach().cpu().numpy().astype('<f4');name_bytes=name.encode('ascii');f.write(struct.pack('<I',len(name_bytes)));f.write(name_bytes);f.write(struct.pack('<II',a.ndim,a.size));f.write(struct.pack('<'+'I'*a.ndim,*a.shape));f.write(a.tobytes());meta.append(dict(name=name,shape=list(a.shape),values=int(a.size)))
    return meta
