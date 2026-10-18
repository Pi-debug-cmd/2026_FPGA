"""Freeze public model revisions/size/SHA before downloading quality reference."""
import concurrent.futures
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
JOBS = [('Plachta/Seed-VC', ['DiT_uvit_tat_xlsr_ema.pth'], '257283f9f41585055e8f858fba4fd044e5caed6e'),
        ('funasr/campplus', ['campplus_cn_common.bin'], None),
        ('FunAudioLLM/CosyVoice-300M', ['hift.pt'], None),
        ('facebook/wav2vec2-xls-r-300m', ['config.json', 'preprocessor_config.json', 'pytorch_model.bin'], None)]


def inspect(job):
    repo, names, revision = job
    url = 'https://huggingface.co/api/models/' + repo + ('/revision/' + revision if revision else '') + '?blobs=true'
    with urllib.request.urlopen(url, timeout=35) as response:
        metadata = json.load(response)
    files = []
    for name in names:
        entry = next(x for x in metadata['siblings'] if x['rfilename'] == name)
        lfs = entry.get('lfs', {})
        files.append({'name': name, 'size': entry['size'], 'sha256': lfs.get('sha256'),
                      'url': 'https://huggingface.co/' + repo + '/resolve/' + metadata['sha'] + '/' + name})
    return {'repository': repo, 'revision': metadata['sha'], 'files': files}


with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    repositories = list(pool.map(inspect, JOBS))
record = {'kind': 'pinned_seed_tiny_asset_plan', 'repositories': repositories,
          'total_bytes': sum(f['size'] for repo in repositories for f in repo['files']),
          'weights_downloaded': False, 'board_deployed': False}
(ROOT / 'report/seed_reference_asset_plan_20261015.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
