"""Author speaker verification weights, pinned revision, D-drive cache only."""
from pathlib import Path
import hashlib
import json
import os
import run_rvc_pilot as pilot

def main():
    pilot.settings()
    os.environ['HF_HUB_DISABLE_XET']='1'
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING']='1'
    from huggingface_hub import HfApi,snapshot_download
    repo='microsoft/wavlm-base-plus-sv'
    info=HfApi().model_info(repo,files_metadata=True)
    files=['config.json','preprocessor_config.json','pytorch_model.bin']
    local=Path(snapshot_download(repo,revision=info.sha,allow_patterns=files,max_workers=3))
    records=[]
    for name in files:
        item=next(x for x in info.siblings if x.rfilename==name)
        digest=hashlib.sha256((local/name).read_bytes()).hexdigest()
        expected=getattr(item.lfs,'sha256',None) if item.lfs else None
        if expected and digest!=expected: raise RuntimeError('Hash mismatch')
        records.append(dict(name=name,bytes=(local/name).stat().st_size,sha256=digest,lfs_sha256=expected))
    out=Path(__file__).resolve().parent/'speaker_evaluator_manifest.json'
    report=dict(repo=repo,revision=info.sha,local_path=str(local),files=records,
                purpose='Relative speaker similarity diagnostics, not human acceptance')
    out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report),flush=True)

if __name__=='__main__': main()
