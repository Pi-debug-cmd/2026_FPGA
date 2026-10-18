"""Run the instrumented host runtime on the fixed 4.32-second input."""
import os
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent
model = root.parent / 'board_budget_20261005' / 'llvc_deploy_model_reduced.bin'
for mode in ('float','int8'):
    env = os.environ.copy()
    if mode == 'float':
        env['LLVC_FLOAT'] = '1'
        env['LLVC_DUMP'] = '1'
        env['LLVC_DUMP_BLOCK'] = '23'  # C counter starts at one; PyTorch block index is zero-based.
    else:
        env.pop('LLVC_FLOAT', None)
        env.pop('LLVC_DUMP', None)
    result = subprocess.run(
        [str(root / 'review_llvc_host_20261008.exe'), str(model)],
        input=(root / 'test' / 'input.bin').read_bytes(),
        capture_output=True,
        cwd=root,
        env=env,
        check=True,
    )
    (root / f'review_{mode}_20261008.bin').write_bytes(result.stdout)
    print(f'{mode}: output_bytes={len(result.stdout)} stderr={result.stderr.decode(errors="replace")}')
