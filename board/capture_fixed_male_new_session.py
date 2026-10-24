"""One-shot fixed-male new-session capture with a 300 ms pre-capture cue."""
from __future__ import annotations

import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
import struct
import time
import wave

from pack_registration_audio import pack_native


RUN = Path("/tmp/codex_fixed_male_new_session_round12_20261024")
SECONDS = 20


def write_cue(path: Path) -> None:
    rate = 44100
    count = round(0.3 * rate)
    fade = round(0.01 * rate)
    samples = [
        int(6553 * min(1.0, index / fade, (count - 1 - index) / fade)
            * math.sin(2 * math.pi * 880 * index / rate))
        for index in range(count)
    ]
    with wave.open(str(path), "wb") as stream:
        stream.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        stream.writeframes(struct.pack(f"<{count}h", *samples))


def pcm_states() -> dict:
    return {
        name: Path("/proc/asound/card0", name, "sub0/status").read_text().strip()
        for name in ("pcm1c", "pcm0p")
    }


def require_idle() -> None:
    states = pcm_states()
    if any(value != "closed" for value in states.values()):
        raise RuntimeError("AUDIO_BUSY: " + json.dumps(states))


def main() -> None:
    RUN.mkdir(parents=True, exist_ok=False)
    require_idle()
    mixer_state = RUN / "mixer_before.state"
    record = {"seconds": SECONDS, "run": str(RUN), "cue_ms": 300, "post_cue_wait_ms": 150}
    saved = False
    try:
        subprocess.run(["alsactl", "-f", str(mixer_state), "store", "0"], check=True, timeout=10)
        saved = True
        controls = [
            ("Left Input Mixer Boost", "on"),
            ("Right Boost Mixer RINPUT1", "on"),
            ("Right Input Mixer Boost", "on"),
            ("Left Boost Mixer LINPUT1", "on"),
            ("Left Input Boost Mixer LINPUT1", "0"),
            ("Capture", "31,31", "cap"),
        ]
        with (RUN / "mixer_setup.log").open("wb") as log:
            for control in controls:
                subprocess.run(["amixer", "sset", *control], stdout=log, stderr=log, check=True, timeout=10)
            subprocess.run(
                ["amixer", "cset", "name=ADC Data Output Select", "1"],
                stdout=log,
                stderr=log,
                check=True,
                timeout=10,
            )
            for control in (
                ("Left Output Mixer PCM", "on"),
                ("Right Output Mixer PCM", "on"),
                ("Headphone Playback ZC", "on"),
                ("Headphone", "127,127"),
                ("Playback", "255,255"),
            ):
                subprocess.run(["amixer", "sset", *control], stdout=log, stderr=log, check=True, timeout=10)

        cue = RUN / "cue300.wav"
        write_cue(cue)
        print("CUE_START", flush=True)
        with (RUN / "cue.log").open("wb") as log:
            subprocess.run(["aplay", "-q", "-D", "default", str(cue)], stdout=log, stderr=log,
                           check=True, timeout=10)
        time.sleep(0.15)
        print("CAPTURE_START seconds=20", flush=True)
        raw_path = RUN / "capture.raw"
        with (RUN / "capture.log").open("wb") as log:
            subprocess.run(
                [
                    "arecord", "-q", "-D", "hw:0,1", "-t", "raw", "-f", "S24_LE",
                    "-r", "32000", "-c", "2", "--period-size=512", "--buffer-size=4096",
                    "-d", str(SECONDS), str(raw_path),
                ],
                stdout=log,
                stderr=log,
                check=True,
                timeout=SECONDS + 10,
            )
        if raw_path.stat().st_size != SECONDS * 32000 * 8:
            raise RuntimeError("Incomplete native capture")
        raw = raw_path.read_bytes()
        wav, clipped = pack_native(raw)
        packed = gzip.compress(wav, compresslevel=9, mtime=0)
        (RUN / "capture.wav.gz").write_bytes(packed)
        record.update(
            {
                "native_clip_fraction": clipped,
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "wav_sha256": hashlib.sha256(wav).hexdigest(),
                "gzip_sha256": hashlib.sha256(packed).hexdigest(),
                "gzip_bytes": len(packed),
            }
        )
        if clipped:
            raise RuntimeError("Native capture contains near-full-scale samples")
        print("CAPTURE_COMPLETE " + json.dumps(record), flush=True)
    finally:
        if saved:
            record["restore_exit"] = subprocess.run(
                ["alsactl", "-f", str(mixer_state), "restore", "0"], timeout=10
            ).returncode
        record["pcm_after"] = pcm_states()
        (RUN / "capture_manifest.json").write_text(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
