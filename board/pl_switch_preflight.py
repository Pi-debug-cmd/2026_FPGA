"""Read-only dependency report before a full PL swap; does not unbind or program."""
import json
from pathlib import Path

devices = Path('/sys/bus/platform/devices')
bound = []
for device in devices.iterdir():
    if device.name.startswith(('43c', '4121', '4160', '42c')) or any(word in device.name for word in ('snd_card', 'drm', 'vcap')):
        driver = device / 'driver'
        bound.append({'device': device.name, 'driver': driver.resolve().name if driver.exists() else None})
processes = []
for path in Path('/proc').iterdir():
    if not path.name.isdigit():
        continue
    try:
        argv = (path / 'cmdline').read_bytes().split(b'\0')
        command = ' '.join(part.decode(errors='replace') for part in argv if part)
        if any(word in command for word in ('music-button', 'music_button', 'aplay ', 'arecord ', 'voice-live')):
            processes.append({'pid': int(path.name), 'command': command})
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        pass
def read(path):
    p = Path(path)
    return p.read_text() if p.exists() else None
record = {'bound_pl_devices': bound, 'audio_processes': processes,
          'gpio_consumers': read('/sys/kernel/debug/gpio'),
          'framebuffer_console': read('/sys/class/vtconsole/vtcon1/name'),
          'manager_flags': read('/sys/class/fpga_manager/fpga0/flags'),
          'manager_state': read('/sys/class/fpga_manager/fpga0/state'),
          'firmware_class_path': read('/sys/module/firmware_class/parameters/path')}
print(json.dumps(record, indent=2))
