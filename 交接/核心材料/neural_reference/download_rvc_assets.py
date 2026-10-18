"""Fetch only six RVC training/inference assets and FFmpeg from author repo.
Pin the Hugging Face revision; verify sizes and published LFS SHA256 values.
No user audio is uploaded.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, urllib.request, shutil

BASE = Path(__file__).resolve().parent
ROOT = BASE / 'RVC'
REPO = 'lj1995/VoiceConversionWebUI'
API = 'https://huggingface.co/api/models/' + REPO

def read_json(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)

def main():
    revision = read_json(API)['sha']
    selected = {
        'hubert_base/config.json': 'assets/hubert_base/config.json',
        'hubert_base/preprocessor_config.json': 'assets/hubert_base/preprocessor_config.json',
        'hubert_base/pytorch_model.bin': 'assets/hubert_base/pytorch_model.bin',
        'pretrained_v2/f0G40k.pth': 'assets/pretrained_v2/f0G40k.pth',
        'pretrained_v2/f0D40k.pth': 'assets/pretrained_v2/f0D40k.pth',
        'rmvpe.pt': 'assets/rmvpe/rmvpe.pt',
        'ffmpeg.exe': 'ffmpeg.exe',
    }
    metadata = {}
    for folder in ['', '/hubert_base', '/pretrained_v2']:
        entries = read_json(API + '/tree/' + revision + folder)
        metadata.update({e['path']: e for e in entries})

    def fetch(pair):
        remote, local = pair
        entry = metadata[remote]
        expected = entry.get('lfs', {}).get('oid')
        path = ROOT / local
        path.parent.mkdir(parents=True, exist_ok=True)
        def valid():
            return path.exists() and path.stat().st_size == entry['size'] and (
                not expected or hashlib.sha256(path.read_bytes()).hexdigest() == expected)
        if not valid():
            print('Downloading ' + remote, flush=True)
            partial = path.with_name(path.name + '.part')
            url = 'https://huggingface.co/' + REPO + '/resolve/' + revision + '/' + remote
            with urllib.request.urlopen(url, timeout=120) as response, partial.open('wb') as out:
                shutil.copyfileobj(response, out, length=1024*1024)
            partial.replace(path)
        if not valid():
            raise RuntimeError('Size or SHA256 mismatch: ' + remote)
        result = dict(path=local, source=remote, size=path.stat().st_size,
                      sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        print('Verified ' + remote, flush=True)
        return result
    with ThreadPoolExecutor(max_workers=3) as pool:
        files = list(pool.map(fetch, selected.items()))
    (BASE / 'rvc_asset_manifest.json').write_text(
        json.dumps(dict(repo=REPO, revision=revision, files=files), indent=2), encoding='utf-8')
    print('All selected assets verified; no audio uploaded.', flush=True)

if __name__ == '__main__':
    main()
