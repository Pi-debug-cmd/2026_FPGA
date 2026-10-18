"""Regression: every sliced utterance must keep its final short chunk."""
import ast
from pathlib import Path
import numpy as np
from scipy import signal

root=Path(__file__).resolve().parent/'RVC'
source=(root/'train'/'preprocess.py').read_text(encoding='utf-8')
parsed=ast.parse(source)
cls=next(n for n in parsed.body if isinstance(n,ast.ClassDef) and n.name=='PreProcess')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='pipeline')
namespace={'load_audio':lambda *args:np.ones(40000),'signal':signal,
           'should_report':lambda *args:False,'println':print,'i18n':lambda x:x}
exec(compile(ast.Module(body=[method],type_ignores=[]),str(root/'train'/'preprocess.py'),'exec'),namespace)
class Fake: pass
class Slicer:
    def slice(self,audio):
        return [np.ones(80000),np.ones(60000)]
obj=Fake()
obj.sr=40000;obj.per=3.7;obj.overlap=.3;obj.tail=4.0
obj.bh=np.ones(1);obj.ah=np.ones(1);obj.slicer=Slicer()
writes=[]
obj.norm_write=lambda audio,key,index:writes.append((len(audio),index))
assert namespace['pipeline'](obj,'unused','case',0,1)
assert writes==[(80000,1),(60000,2)],writes
print('PASS: both sliced utterance tails preserved:',writes)
