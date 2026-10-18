"""Interrupt a board-console foreground benchmark and show resulting prompt."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'native_llvc_20261005' / 'transport_lib'))
import serial

port = serial.Serial(sys.argv[1] if len(sys.argv) > 1 else 'COM9', 115200, timeout=0.2)
try:
    port.write(b'\x03')
    time.sleep(0.6)
    port.write(b'\r')
    end = time.monotonic() + 3
    while time.monotonic() < end:
        data = port.read(max(1, port.in_waiting))
        if data:
            print(data.decode(errors='replace'), end='', flush=True)
finally:
    port.close()
