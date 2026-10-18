"""Volatile full-PL test loader for the reviewed board; never updates boot files."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

argument = Path(sys.argv[1])
run = argument.resolve()
if (argument.parent != Path('/tmp') or not argument.name.startswith('codex_')
        or run.parent != Path('/tmp').resolve() or not run.is_dir()):
    raise SystemExit('Use an existing project /tmp staging directory')
record = json.loads((run / 'manifest.json').read_text())
for name in ['audio_pitch_dma_swap.bin', 'pitch_dma_proxy.ko', 'pitch_dma_control_overlay.dtbo']:
    item = record['files'][name]
    data = (run / name).read_bytes()
    assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'], name
assert record['part'] == 'xc7z020clg400-2' and record['control_base'] == '0x41200000'
assert not Path('/dev/pitch_dma').exists(), 'Remove previous DMA test first'
assert not Path('/sys/module/pitch_dma_proxy').exists(), 'Unload previous test module first'
assert not Path('/sys/kernel/config/device-tree/overlays/codex_pitch_control').exists()
for node in ['pcm1c', 'pcm0p']:
    assert Path('/proc/asound/card0', node, 'sub0/status').read_text().strip() == 'closed'
listeners = []
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():
        continue
    try:
        command = (proc / 'cmdline').read_bytes().split(b'\0')
        if command[:2] == [b'/bin/sh', b'/usr/local/bin/music-button-listener.sh']:
            listeners.append(int(proc.name))
    except (FileNotFoundError, ProcessLookupError):
        pass
assert len(listeners) == 1, 'Recheck factory listener'
devices = Path('/sys/bus/platform/devices')
order = ['xlnx_snd_card.0.auto', 'gpio-keys', 'xlnx-drm.0',
         'amba_pl:drm_pl_disp_hdmi', 'amba_pl:vcap_dvp',
         '43c70000.v_frmbuf_rd', '43ca0000.v_frmbuf_rd', '43cb0000.v_frmbuf_wr',
         '43c00000.v_tc', '43c80000.v_tc', '43c40000.audio_formatter',
         '43c50000.i2s_receiver', '43c60000.i2s_transmitter',
         '43c20000.axi_dynclk', '43c90000.axi_dynclk',
         '41600000.i2c', '42c00000.serial', '41210000.gpio']
bindings = {dev: (devices / dev / 'driver').resolve().name
            for dev in order if (devices / dev / 'driver').exists()}
for dev in devices.iterdir():
    if dev.name.startswith(('43c', '412', '416', '42c')) and (dev / 'driver').exists():
        assert dev.name in bindings, f'Unreviewed PL consumer: {dev.name}'
journal = run / 'switch_state.json'
assert not journal.exists(), 'Inspect existing switch journal before reuse'
state = {'listener_pid': listeners[0], 'original_bindings': bindings,
         'stage': 'preflight', 'full_recovery': 'cold boot; do not hot-bind camera'}
def checkpoint(stage):
    state['stage'] = stage
    journal.write_text(json.dumps(state, indent=2) + '\n')
    print(stage, flush=True)
checkpoint('preflight')
subprocess.run(['alsactl', '-f', str(run / 'mixer_before.state'), 'store', '0'], check=True)
signal_pid = listeners[0]
os.kill(signal_pid, signal.SIGSTOP)
checkpoint('listener_paused')
for dev in order:
    driver = devices / dev / 'driver'
    if driver.exists():
        (driver.resolve() / 'unbind').write_text(dev)
checkpoint('old_pl_consumers_unbound')
firmware_path = Path('/sys/module/firmware_class/parameters/path')
oldpath = firmware_path.read_text().strip() or '/lib/firmware'
try:
    firmware_path.write_text(str(run))
    Path('/sys/class/fpga_manager/fpga0/flags').write_text('0')
    Path('/sys/class/fpga_manager/fpga0/firmware').write_text('audio_pitch_dma_swap.bin')
finally:
    firmware_path.write_text(oldpath)
assert Path('/sys/class/fpga_manager/fpga0/state').read_text().strip() == 'operating'
checkpoint('candidate_loaded')
# Driver-core deferred probing may bind peers automatically.
for dev in ['43c20000.axi_dynclk', '43c50000.i2s_receiver',
            '43c60000.i2s_transmitter', '43c40000.audio_formatter', 'xlnx_snd_card.0.auto']:
    if not (devices / dev / 'driver').exists():
        try:
            Path('/sys/bus/platform/drivers', bindings[dev], 'bind').write_text(dev)
        except OSError:
            time.sleep(1)
    assert (devices / dev / 'driver').exists(), f'Audio rebind failed: {dev}'
deadline = time.monotonic() + 10
while not Path('/dev/snd/controlC0').exists():
    assert time.monotonic() < deadline, 'Sound card registration timeout'
    time.sleep(0.1)
checkpoint('audio_card_registered')
subprocess.run(['alsactl', '-f', str(run / 'mixer_before.state'), 'restore', '0'], check=True)
subprocess.run(['insmod', str(run / 'pitch_dma_proxy.ko')], check=True)
overlay = Path('/sys/kernel/config/device-tree/overlays/codex_pitch_control')
overlay.mkdir()
(overlay / 'dtbo').write_bytes((run / 'pitch_dma_control_overlay.dtbo').read_bytes())
assert Path('/dev/pitch_dma').exists()
checkpoint('ready_for_v2_numeric_test')
