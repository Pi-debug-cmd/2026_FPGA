#!/usr/bin/env python3
"""Volatile full-PL load of the 2018-10-25 Vivado 2018.3 bitstream.

Records the current PL/audio/driver state first, pauses the factory audio
listener, unbinds every PL consumer that does not exist in the new design,
loads the byte-swapped image through fpga_manager, then rebinds the audio
stack.  Nothing outside /tmp is written; the boot partition is only read.
Python 3.8 compatible.  Must run as root.
"""
import hashlib
import json
import os
import signal
import struct
import subprocess
import sys
import time
from pathlib import Path

RUN = Path(sys.argv[1])
FW = Path(sys.argv[2]) if len(sys.argv) > 2 else RUN / 'audio_pitch_dma_2018_swap.bin'
JOURNAL = RUN / 'switch_state.json'
DEVICES = Path('/sys/bus/platform/devices')

# upper-level consumers first, leaves last (order from board/load_pitch_candidate.py)
UNBIND = [
    ('platform', 'xlnx_snd_card.0.auto'),
    ('platform', 'gpio-keys'),
    ('platform', 'xlnx-drm.0'),
    ('platform', 'amba_pl:drm_pl_disp_hdmi'),
    ('platform', 'amba_pl:vcap_dvp'),
    ('platform', '43c70000.v_frmbuf_rd'),
    ('platform', '43ca0000.v_frmbuf_rd'),
    ('platform', '43cb0000.v_frmbuf_wr'),
    ('platform', '43c00000.v_tc'),
    ('platform', '43c80000.v_tc'),
    ('platform', '43c40000.audio_formatter'),
    ('platform', '43c50000.i2s_receiver'),
    ('platform', '43c60000.i2s_transmitter'),
    ('platform', '43c20000.axi_dynclk'),
    ('platform', '43c90000.axi_dynclk'),
    ('platform', '41600000.i2c'),
    ('platform', '42c00000.serial'),
    ('platform', '41210000.gpio'),
]
REBIND = ['41600000.i2c', '43c20000.axi_dynclk', '43c50000.i2s_receiver',
          '43c60000.i2s_transmitter', '43c40000.audio_formatter',
          'xlnx_snd_card.0.auto']

state = {'fw': str(FW), 'stage': 'start', 'unbound': [], 'rebound': [], 'paused': []}


def save():
    JOURNAL.write_text(json.dumps(state, indent=2) + '\n')


def note(stage, **extra):
    state.update(extra)
    state['stage'] = stage
    save()
    print('STAGE', stage, json.dumps(extra, sort_keys=True), flush=True)


def out(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def driver_of(dev):
    link = DEVICES / dev / 'driver'
    return link.resolve().name if link.exists() else None


def unbind(dev):
    drv = driver_of(dev)
    if not drv:
        return 'absent'
    try:
        Path('/sys/bus/platform/drivers', drv, 'unbind').write_text(dev)
    except OSError as e:
        return 'error:%s' % e
    return 'unbound:' + drv


def bind(dev):
    drv = state['bindings'].get(dev)
    if not drv:
        return 'unknown-driver'
    if driver_of(dev):
        return 'already'
    try:
        Path('/sys/bus/platform/drivers', drv, 'bind').write_text(dev)
    except OSError as e:
        if driver_of(dev):
            return 'auto'
        return 'error:%s' % e
    return 'bound'


def read_text(p):
    try:
        return Path(p).read_text().strip()
    except OSError:
        return None


def main():
    if not FW.is_file():
        raise SystemExit('missing firmware %s' % FW)
    raw = FW.read_bytes()
    state['fw_bytes'] = len(raw)
    state['fw_sha256'] = hashlib.sha256(raw).hexdigest()
    assert len(raw) % 4 == 0 and b'\x66\x55\x99\xaa' in raw[:256], 'not a swapped zynq image'
    state['fpga_state_before'] = read_text('/sys/class/fpga_manager/fpga0/state')
    state['panic_before'] = read_text('/proc/sys/kernel/panic')
    state['panic_on_oops_before'] = read_text('/proc/sys/kernel/panic_on_oops')
    state['bindings'] = {}
    for dev in DEVICES.iterdir():
        drv = driver_of(dev.name)
        if drv:
            state['bindings'][dev.name] = drv
    state['amba_pl'] = sorted(p.name for p in Path('/proc/device-tree/amba_pl').iterdir()) \
        if Path('/proc/device-tree/amba_pl').is_dir() else []
    for node in ['pcm1c', 'pcm0p']:
        state['pcm_' + node] = read_text('/proc/asound/card0/%s/sub0/status' % node)
    _, state['dmesg_tail_before'] = out(['dmesg'])
    state['dmesg_tail_before'] = state['dmesg_tail_before'][-1500:]
    save()
    note('state_recorded')

    out(['alsactl', '-f', str(RUN / 'mixer_before.state'), 'store', '0'])
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        try:
            cmd = (entry / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
        except OSError:
            continue
        if 'music-button-listener' in cmd:
            os.kill(int(entry.name), signal.SIGSTOP)
            state['paused'].append(int(entry.name))
        elif cmd.startswith('aplay') or cmd.startswith('arecord') or 'aplay ' in cmd:
            try:
                os.kill(int(entry.name), signal.SIGKILL)
            except OSError:
                pass
    note('listener_paused', paused=state['paused'])

    for _, dev in UNBIND:
        r = unbind(dev)
        state['unbound'].append('%s=%s' % (dev, r))
        print('UNBIND', dev, r, flush=True)
    note('old_pl_consumers_unbound')

    # any oops from a stale consumer must self-recover by reboot (U-Boot reloads factory bit)
    Path('/proc/sys/kernel/panic').write_text('10')
    oldpath = read_text('/sys/module/firmware_class/parameters/path') or ''
    try:
        Path('/sys/module/firmware_class/parameters/path').write_text(str(RUN))
        Path('/sys/class/fpga_manager/fpga0/flags').write_text('0')
        Path('/sys/class/fpga_manager/fpga0/firmware').write_text(FW.name)
    finally:
        try:
            Path('/sys/module/firmware_class/parameters/path').write_text(oldpath)
        except OSError:
            Path('/sys/module/firmware_class/parameters/path').write_text('/lib/firmware')
    state['firmware_class_path_after'] = read_text('/sys/module/firmware_class/parameters/path')
    time.sleep(0.3)
    after = read_text('/sys/class/fpga_manager/fpga0/state')
    state['fpga_state_after'] = after
    note('bitstream_loaded')
    if after != 'operating':
        _, state['dmesg_load'] = out(['dmesg'])
        state['dmesg_load'] = state['dmesg_load'][-2000:]
        save()
        raise SystemExit('fpga_manager state=%r' % after)

    for dev in REBIND:
        r = bind(dev)
        state['rebound'].append('%s=%s' % (dev, r))
        print('BIND', dev, r, flush=True)
        time.sleep(0.2)
    note('audio_rebound')

    deadline = time.monotonic() + 15
    while not Path('/dev/snd/controlC0').exists() and time.monotonic() < deadline:
        time.sleep(0.2)
    state['sound_control'] = Path('/dev/snd/controlC0').exists()
    out(['alsactl', '-f', str(RUN / 'mixer_before.state'), 'restore', '0'])
    _, state['dmesg_tail_after'] = out(['dmesg'])
    state['dmesg_tail_after'] = state['dmesg_tail_after'][-2000:]
    note('done', sound_control=state['sound_control'])
    print(json.dumps({k: v for k, v in state.items() if k.startswith('fpga')}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:  # noqa: BLE001
        state['exception'] = repr(exc)
        save()
        raise
