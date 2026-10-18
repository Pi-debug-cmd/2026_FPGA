"""Reset only the idle audio driver/codec chain; preserve PL and DMA control."""
import json
from pathlib import Path
import subprocess
import time

run = Path('/tmp/codex_pl_control_20261011/audio_reset1')
for name in ['pcm1c', 'pcm0p']:
    assert Path('/proc/asound/card0', name, 'sub0/status').read_text().strip() == 'closed'
run.mkdir()
subprocess.run(['alsactl', '-f', str(run / 'before.state'), 'store', '0'], check=True)
devices = Path('/sys/bus/platform/devices')
order = ['xlnx_snd_card.0.auto', '43c40000.audio_formatter',
         '43c50000.i2s_receiver', '43c60000.i2s_transmitter', '43c20000.axi_dynclk']
original = {name: (devices / name / 'driver').resolve().name for name in order}
(run / 'bindings.json').write_text(json.dumps(original, indent=2))
for name in order:
    driver = devices / name / 'driver'
    if driver.exists():
        print('UNBIND', name, flush=True)
        (driver.resolve() / 'unbind').write_text(name)
codec = Path('/sys/bus/i2c/devices/0-001a/driver')
driver = codec.resolve()
assert driver.name == 'wm8960'
(driver / 'unbind').write_text('0-001a')
(driver / 'bind').write_text('0-001a')
print('CODEC_REPROBED', flush=True)
for name in ['43c20000.axi_dynclk', '43c50000.i2s_receiver',
             '43c60000.i2s_transmitter', '43c40000.audio_formatter', 'xlnx_snd_card.0.auto']:
    if not (devices / name / 'driver').exists():
        try:
            Path('/sys/bus/platform/drivers', original[name], 'bind').write_text(name)
        except OSError:
            time.sleep(1)
    assert (devices / name / 'driver').exists(), name
deadline = time.monotonic() + 10
while not Path('/dev/snd/controlC0').exists():
    assert time.monotonic() < deadline, 'Soundcard reprobe timeout'
    time.sleep(0.1)
subprocess.run(['alsactl', '-f', str(run / 'before.state'), 'restore', '0'], check=True)
print('AUDIO_REINITIALIZED', flush=True)
