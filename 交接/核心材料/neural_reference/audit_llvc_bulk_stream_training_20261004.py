"""Check whether bulk-training outputs represent the deployed chunk contract."""
from pilot_phasefree_student_20261004 import OUT,TEACHER,stream,load_model,read_audio,digest
import json,torch,numpy as np
torch.set_num_threads(4)
rows=json.loads((TEACHER/'evaluation_items.json').read_text(encoding='utf8'))
source=next(r for r in rows if r['source_split']=='development')
wave=read_audio(source['source_path']);records=[]
for kind in ['official_pretrained','phasefree_step20']:
    model,_=load_model()
    if kind=='phasefree_step20':model.load_state_dict(torch.load(OUT/'checkpoint_step20.pt',map_location='cpu',weights_only=True)['model'],strict=True)
    with torch.inference_mode():bulk=model(torch.tensor(wave)[None,None]).numpy().reshape(-1)
    online=stream(model,wave)
    assert len(bulk)==len(online)==len(wave)
    segments=[]
    for begin in [0,.1,.5,1.]:
        a,b=bulk[int(begin*16000):],online[int(begin*16000):]
        segments.append(dict(begin_seconds=begin,normalized_rmse=float(np.linalg.norm(a-b)/max(np.linalg.norm(a),1e-12)),
                             maximum_absolute_error=float(np.max(np.abs(a-b)))))
    records.append(dict(model=kind,segments=segments,bulk_and_stream_sample_equal=bool(np.array_equal(bulk,online))))
    print(kind,segments,flush=True)
(OUT/'bulk_stream_contract_audit.json').write_text(json.dumps(dict(status='observed_output_contract_comparison',source_path=source['source_path'],
    source_sha256=digest(source['source_path']),comparisons=records,not_target_voice_acceptance=True),indent=2),encoding='utf8')
