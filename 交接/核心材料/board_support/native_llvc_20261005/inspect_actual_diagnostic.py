from pathlib import Path
import json,tarfile,hashlib
import numpy as np
import soundfile as sf
r=Path(__file__).resolve().parent
out=r/'actual_mic_diagnostic_20261005a';out.mkdir(exist_ok=True)
with tarfile.open(r/'mic_diagnostic_20261005a.tar.gz') as t:
    for m in t.getmembers():
        assert m.name in ['mic_diagnostic_20261005a.input.s16','mic_diagnostic_20261005a.output.s16','mic_diagnostic_20261005a.json','mic_diagnostic_20261005a.status.json']
        assert m.isfile();(out/m.name).write_bytes(t.extractfile(m).read())
meta=json.loads((out/'mic_diagnostic_20261005a.json').read_text())
rows=[]
for role in ['input','output']:
    p=out/('mic_diagnostic_20261005a.'+role+'.s16');v=np.fromfile(p,dtype='<i2');x=v.astype('float64')/32768
    assert len(x)==meta['samples']
    values,counts=np.unique(v,return_counts=True);order=np.argsort(-counts)
    blocks=x[:len(x)//1600*1600].reshape(-1,1600);levels=np.sqrt(np.mean(blocks*blocks,axis=1))
    sf.write(out/(role+'.wav'),x,16000,subtype='PCM_16')
    rows.append({'role':role,'samples':len(x),'rms':float(np.sqrt(np.mean(x*x))),'peak':float(np.max(np.abs(x))),
       'dc':float(x.mean()),'std':float(x.std()),'unique_pcm_values':len(values),
       'most_common_values':[(int(values[i]),int(counts[i])) for i in order[:10]],
       'frame_100ms_rms_max':float(levels.max()),'frame_100ms_rms_min':float(levels.min()),
       'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'wav':str(out/(role+'.wav'))})
report={'manifest':meta,'signals':rows,'diagnostic_only_not_speaker_enrollment':True}
(out/'signal_inspection.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
