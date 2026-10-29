"""Restore pinned public teacher assets under a single task workspace."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

REVISION = '29e01c4e8d000f4bcd70751be16fa94bf3d85a18'
REPOSITORY = 'FunAudioLLM/Fun-CosyVoice3-0.5B-2512'
NAMES = ['cosyvoice3.yaml', 'config.json', 'configuration.json', 'README.md',
         'campplus.onnx', 'speech_tokenizer_v3.onnx', 'llm.pt', 'flow.pt', 'hift.pt']
NAMES += ['CosyVoice-BlankEN/' + n for n in
          ['config.json', 'generation_config.json', 'merges.txt', 'tokenizer_config.json', 'vocab.json']]


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, type=Path)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    out = workspace / 'models/Fun-CosyVoice3-0.5B-2512'
    out.mkdir(parents=True, exist_ok=True)
    url = f'https://huggingface.co/api/models/{REPOSITORY}/revision/{REVISION}?blobs=true'
    with urllib.request.urlopen(url, timeout=45) as response:
        metadata = json.load(response)
    assert metadata['sha'] == REVISION
    (out.parent / 'repository_metadata.json').write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    selected = [next(r for r in metadata['siblings'] if r['rfilename'] == n) for n in NAMES]
    needed = sum(r['size'] for r in selected)
    assert shutil.disk_usage(workspace).free > needed + 10 * 1024 ** 3
    records = []
    for row in selected:
        name = row['rfilename']
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        expected = row.get('lfs', {}).get('sha256')
        if not path.exists():
            partial = path.with_name(path.name + '.part')
            offset = partial.stat().st_size if partial.exists() else 0
            request = urllib.request.Request(
                f'https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/{name}',
                headers={'Range': f'bytes={offset}-'} if offset else {})
            with urllib.request.urlopen(request, timeout=60) as response:
                if offset and response.status != 206:
                    raise RuntimeError(f'Server ignored resume range for {name}')
                if offset and not response.headers.get('Content-Range', '').startswith(f'bytes {offset}-'):
                    raise RuntimeError(f'Invalid resume offset for {name}')
                print('DOWNLOADING', name, offset, row['size'], flush=True)
                with partial.open('ab' if offset else 'wb') as stream:
                    checkpoint = offset
                    while block := response.read(4 * 1024 * 1024):
                        stream.write(block)
                        offset += len(block)
                        if offset - checkpoint >= 64 * 1024 * 1024:
                            print('BYTES', name, offset, row['size'], flush=True)
                            checkpoint = offset
            assert partial.stat().st_size == row['size'], name
            if expected:
                assert sha(partial) == expected, name
            partial.replace(path)
        assert path.stat().st_size == row['size'], name
        digest = sha(path)
        if expected:
            assert digest == expected, name
        records.append({'name': name, 'bytes': row['size'], 'sha256': digest,
                        'expected_lfs_sha256': expected})
        (out.parent / 'asset_manifest.json').write_text(json.dumps({
            'repository': REPOSITORY, 'revision': REVISION, 'files': records,
            'complete': len(records) == len(NAMES), 'inference_tested': False,
        }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('VERIFIED', name, digest, flush=True)


if __name__ == '__main__':
    main()
