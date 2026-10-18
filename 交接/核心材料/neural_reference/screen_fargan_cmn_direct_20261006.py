from pathlib import Path
from fargan_feature_mapper_20261006 import normalize_spectrum
import numpy as np,json,subprocess,soundfile as sf
base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';native=base.parent/'board_support/native_llvc_20261005';out=budget/'fargan_cmn_direct';out.mkdir(exist_ok=True)
corpus=json.loads((budget/'fargan_corpus/manifest.json').read_text(encoding='utf-8'));reference=np.array(json.loads((budget/'fargan_corpus/target_spectral_reference.json').read_text())['reference'],dtype=np.float32);rows=[]
for row in [r for r in corpus['files'] if r['split']=='validation']:
 x=np.fromfile(row['source_features'],dtype=np.float32).reshape(-1,20);y=normalize_spectrum(x,reference);stem=Path(row['filename']).stem;features=out/(stem+'.converted.f32');y.tofile(features);pcm=out/(stem+'.pcm')
 subprocess.run([str(native/'fargan_probe_host.exe'),'--synthesis',str(features),str(pcm),str(out/(stem+'.synthesis.json'))],check=True)
 wave=np.fromfile(pcm,dtype='<i2').astype('float32')/32768;path=out/(stem+'_student.wav');sf.write(path,wave,16000,subtype='FLOAT');rows.append(dict(row,student_path=str(path)))
(out/'decision.json').write_text(json.dumps(dict(complete=True,heldout_outputs=rows,source_enrollment=False,statistical_causal_feature_conversion=True,learned_target_mapper=False,neural_vocoder=True,source_waveform_bypass=False,recognizer_used_as_loss=False,auxiliary_speaker_loss_used=False,quality_accepted=False,board_live_deployed=False),ensure_ascii=False,indent=2),encoding='utf-8');print('CMN_DIRECT_RENDERED',flush=True)
