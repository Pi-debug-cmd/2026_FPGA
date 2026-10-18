from pathlib import Path
import json
import numpy as np
import soundfile as sf
r=Path(__file__).resolve().parent
manifest=r.parents[1]/'board_budget_20261005/student_corpus/paired_manifest.json'
data=json.loads(manifest.read_text(encoding='utf-8'));rows=[]
for row in data['files']:
    if row['split']!='train':continue
    x,sr=sf.read(row['path'],dtype='float32');x=x.mean(axis=1) if x.ndim==2 else x
    hop=sr//50;frames=x[:len(x)//hop*hop].reshape(-1,hop);levels=np.sqrt(np.mean(frames*frames,axis=1))
    rows.append({'filename':row['filename'],'rms':float(np.sqrt(np.mean(x*x))), 'peak':float(np.max(np.abs(x))), 'frame_rms_p90':float(np.percentile(levels,90))})
values=np.array([row['rms'] for row in rows])
result={'train_files':len(rows),'source_waveforms_not_normalized_in_training':True,
 'augmentation_gain_min':.35,'augmentation_gain_max':1.35,
 'whole_file_rms_min_median_max':[float(values.min()),float(np.median(values)),float(values.max())],
 'rows':rows,'whole_file_vs_one_second_live_windows_not_strictly_equivalent':True}
(r/'training_input_level_diagnosis.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
