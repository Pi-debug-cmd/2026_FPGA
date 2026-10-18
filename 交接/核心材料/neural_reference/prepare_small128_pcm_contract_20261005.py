from train_board_student_20261005 import BASE,build_small,stream
from pathlib import Path
import numpy as np,torch,tarfile,json,hashlib
torch.set_num_threads(4)
root=BASE.parent/'board_support/native_llvc_20261005';model,cfg,_=build_small(128)
records=[]
for case in ['edge_209','real_16000']:
 raw=np.fromfile(root/(case+'.input.f32'),dtype='<f4')
 pcm=np.rint(np.clip(raw,-1,32767/32768)*32768).astype('<i2');pcm.tofile(root/(case+'.small128_contract.input.s16'))
 y=stream(model,pcm.astype('float32')/32768)
 expected=np.rint(np.clip(y,-1,32767/32768)*32768).astype('<i2');expected.tofile(root/(case+'.small128_contract.torch.s16'))
 records.append(dict(case=case,samples=len(raw)))
bundle=root/'small128_pcm_contract.tar.gz'
with tarfile.open(bundle,'w:gz') as tar:
 for r in records:
  name=r['case']+'.small128_contract.input.s16';tar.add(root/name,arcname=name)
(root/'small128_pcm_contract.json').write_text(json.dumps(dict(cases=records,bundle_sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(),scope='Synthetic and existing public file input only, no mic capture'),indent=2))
print('PCM_CONTRACT_PREPARED',flush=True)
