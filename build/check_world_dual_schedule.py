"""PCM invariance, bounded backpressure, wraparound and deadline failure checks."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from src.reference.audio_io import write_pcm16

base = root / "build/generated/world_budget/dual_checks"
base.mkdir(exist_ok=True)
dual = root / "build/generated/world_budget/world_dual_native_v11.exe"
serial = root / "build/generated/world_budget/world_sliding_native_v10.exe"
speech = root / "build/generated/world_budget/input16k.wav"
silence = base / "silence.wav"
transition = base / "transitions.wav"
write_pcm16(silence, np.zeros(8000))
t = np.arange(32000) / 16000
phase = 2 * np.pi * np.cumsum(160 + 55 * np.sin(2 * np.pi * t)) / 16000
signal = .1 * np.sin(phase) + .03 * np.sin(2 * phase)
signal[(t > .7) & (t < 1.1)] = 0
write_pcm16(transition, signal)

results = []
def run(name, source, hop, repeat=1, mode="burst", delay=160, slots=1, pause=0, expected=0, reference=None):
    output = base / (name + ".wav")
    command = [str(dual), str(source), str(output), str(hop), str(repeat), mode,
               str(delay), str(slots), str(pause)]
    process = subprocess.run(command, capture_output=True, text=True, timeout=90)
    if process.returncode != expected:
        raise RuntimeError(f"{name}: exit {process.returncode}, {process.stdout}, {process.stderr}")
    record = json.loads(process.stdout)
    if record["max_queue"] > slots or record["max_live_parameters"] > 16:
        raise AssertionError("Queue/lifetime bound violated")
    if record["submitted"] != record["consumed"]:
        raise AssertionError("Dropped parameters")
    if reference is not None:
        if output.read_bytes() != reference.read_bytes():
            raise AssertionError(f"{name}: PCM differs from serial/reference output")
    record.update(name=name, exit_code=process.returncode,
                  wav_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                  matches_reference=reference is not None)
    results.append(record)
    return output

for source in [speech, silence, transition]:
    for hop in [30, 40]:
        reference = base / f"{source.stem}_{hop}_serial.wav"
        command = [str(serial), str(source), str(reference)] + (["hop40"] if hop == 40 else [])
        subprocess.run(command, capture_output=True, check=True, timeout=30)
        run(f"{source.stem}_{hop}_burst", source, hop, reference=reference)

for hop in [30, 40]:
    reference = base / f"input16k_{hop}_serial.wav"
    run(f"speech_{hop}_paced", speech, hop, mode="paced", reference=reference)

# Enough blocks to wrap WORLD's 16 slots hundreds of times; every run restarts state.
for hop in [30, 40]:
    reference = run(f"sustained_{hop}_queue8", speech, hop, repeat=12, slots=8)
    run(f"sustained_{hop}_queue1", speech, hop, repeat=12, reference=reference)

run("injected_consumer_stall", speech, 40, mode="paced", pause=200, expected=6,
    reference=base / "input16k_40_serial.wav")
record = {"checks": results, "limitation": "Windows host file scheduling; no ARM budget, live I/O or measured latency evidence"}
destination = root / "report/world_dual_host_checks_20261013.json"
destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"checks_passed": len(results), "report": str(destination)}))
