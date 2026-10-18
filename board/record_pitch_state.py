"""Record the completed trial state; changes only the project journal in /tmp."""
import json
from pathlib import Path
import sys

argument = Path(sys.argv[1])
run = argument.resolve()
assert argument.parent == Path('/tmp') and argument.name.startswith('codex_')
assert run.parent == Path('/tmp').resolve()
journal = run / 'switch_state.json'
state = json.loads(journal.read_text())
state['fpga_state'] = Path('/sys/class/fpga_manager/fpga0/state').read_text().strip()
state['pcm_states'] = {node: Path('/proc/asound/card0', node, 'sub0/status').read_text().strip()
                       for node in ['pcm1c', 'pcm0p']}
assert state['fpga_state'] == 'operating'
assert set(state['pcm_states'].values()) == {'closed'}
state['stage'] = 'numeric_passed_listening_completed_await_feedback'
state['dma_device_present'] = Path('/dev/pitch_dma').exists()
state['listener_status'] = Path('/proc', str(state['listener_pid']), 'status').read_text().split('State:')[1].splitlines()[0].strip()
journal.write_text(json.dumps(state, indent=2) + '\n')
print(json.dumps(state, indent=2))
