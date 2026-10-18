"""Automatic past-only channel/voice context; not source enrollment.
Inputs: original21 + past200 active cepstral mean17 + count confidence1.
No future frame, whole-utterance statistic or extra source reference at runtime.
"""
from fargan_mapper_v8_20261006 import MapperV8,pitch_aware_features
import numpy as np, torch
from torch import nn

def context_features(raw):
    x=pitch_aware_features(raw);contexts=np.zeros((len(raw),18),dtype='float32')
    history=np.zeros((200,17),dtype='float64');total=np.zeros(17,dtype='float64')
    count=slot=quiet=0
    for i,row in enumerate(raw):
        if row[0]>-7:
            quiet=0
            if count<200:history[count]=row[1:18];total+=row[1:18];count+=1
            else:total-=history[slot];history[slot]=row[1:18];total+=row[1:18];slot=(slot+1)%200
        elif row[0]<-9 or row[19]<-.2:
            quiet+=1
            if quiet>80:count=slot=0;total[:]=0
        if count:contexts[i,:17]=total/count
        contexts[i,17]=count/200.
    return np.concatenate([x,contexts],axis=1)

class MapperContext(MapperV8):
    format_version=9
    def __init__(self,mean,std):
        super().__init__(mean,std);self.pre=nn.Linear(39,128)
