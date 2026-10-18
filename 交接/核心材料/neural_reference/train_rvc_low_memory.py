"""Run the upstream trainer with zero DataLoader worker processes on Windows.
Prevents four redundant Torch/CUDA imports and large prefetched shared buffers.
Model, optimizer, losses and minibatch size are unchanged.
"""
import runpy
import torch.utils.data

upstream_loader=torch.utils.data.DataLoader
def low_memory_loader(*args,**kwargs):
    kwargs['num_workers']=0
    kwargs['persistent_workers']=False
    kwargs.pop('prefetch_factor',None)
    return upstream_loader(*args,**kwargs)

torch.utils.data.DataLoader=low_memory_loader
if __name__=='__main__':
    runpy.run_module('train.train',run_name='__main__')
