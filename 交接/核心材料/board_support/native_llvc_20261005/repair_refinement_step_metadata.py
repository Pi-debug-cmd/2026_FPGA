from pathlib import Path
import hashlib,json,torch
r=Path(__file__).resolve().parent
out=r.parents[1]/'board_budget_20261005/small96_noise_refinement'
assert json.loads((out/'decision.json').read_text(encoding='utf-8'))['complete']
rows=[]
def model_sha(s):
    h=hashlib.sha256()
    for key,tensor in sorted(s.items()):h.update(key.encode());h.update(tensor.numpy().tobytes())
    return h.hexdigest()
for n in [400,800,1200]:
    p=out/('checkpoint_step'+str(n)+'.pt');x=torch.load(p,map_location='cpu',weights_only=True)
    before=x['total_after_structural_initialization_steps'];digest=model_sha(x['model'])
    x['total_after_structural_initialization_steps']=8000+n
    if before!=8000+n:torch.save(x,p)
    y=torch.load(p,map_location='cpu',weights_only=True);assert model_sha(y['model'])==digest
    rows.append({'checkpoint':p.name,'prior_total_field':before,'correct_total_field':8000+n,'all_model_tensors_unchanged':True})
(out/'checkpoint_metadata_repair.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(rows))
