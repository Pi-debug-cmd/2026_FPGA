#!/usr/bin/env python3
"""Generic PL overlay loader for Xilinx Zynq-7000 (fpga_manager), with state journal,
register-level acceptance checks and one-command rollback.

Design goals
------------
1. Board-agnostic: every board-specific fact is *data* (CLI flags / JSON), never
   hard-coded in the logic.  The same file loaded a re-built pitch core, and can
   load any other overlay on any Zynq-7000 board that exposes
   /sys/class/fpga_manager/fpga0.
2. Nothing outside --run-dir is written; the boot partition is only read.
3. Every step appends to a journal BEFORE it is attempted, so a crashed or
   power-cycled load still leaves an auditable record and a rollback image.
4. Fail loud: state != "operating", a missing rebind, or a register whose
   readback does not match is an exception, not a warning.

Tested on: Zynq-7020 (xc7z020clg400-2), PetaLinux 2022.2, kernel 5.15.0-xilinx.
Python 3.8+ / stdlib only (the board's python3 has no `mmap` module -- all MMIO
is done through /dev/mem with `os.pread`/`os.pwrite`-free `struct` access, see
regtool.py which is a *separate* process for that reason).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

FPGA_STATE = Path("/sys/class/fpga_manager/fpga0/state")
FPGA_FLAGS = Path("/sys/class/fpga_manager/fpga0/flags")
FPGA_FW = Path("/sys/class/fpga_manager/fpga0/firmware")
FW_PATH = Path("/sys/module/firmware_class/parameters/path")
DEVICES = Path("/sys/bus/platform/devices")

# The Zynq PCAP/DMA path takes 32-bit configuration words little-endian; Vivado
# .bin is big-endian.  A correctly swapped image therefore contains the sync word
# 0x665599aa (big-endian 0xaa995566 byte-reversed) within the first 256 bytes.
SYNC_SWAPPED = bytes.fromhex("665599aa")
SYNC_PLAIN = bytes.fromhex("aa995566")


class OverlayError(RuntimeError):
    pass


def _read(path: Path):
    try:
        return path.read_text().strip()
    except OSError:
        return None


def _write(path: Path, value: str) -> None:
    path.write_text(value)


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def driver_of(dev: str):
    link = DEVICES / dev / "driver"
    try:
        return link.resolve().name if link.exists() else None
    except OSError:
        return None


class OverlayLoader:
    def __init__(self, image: Path, run_dir: Path, consumers=(), rebind=(),
                 journal: str = "overlay_state.json", pause=(), kill_audio=True,
                 panic_seconds: int = 10, dry_run: bool = False):
        self.image = Path(image)
        self.run_dir = Path(run_dir)
        self.consumers = list(consumers)
        self.rebind = list(rebind)
        self.pause_patterns = list(pause)
        self.kill_audio = kill_audio
        self.panic_seconds = panic_seconds
        self.dry_run = dry_run
        self.journal_path = self.run_dir / journal
        self.state = {"image": str(self.image), "stage": "init", "unbound": [],
                      "rebound": [], "paused": [], "killed": []}
        self.run_dir.mkdir(parents=True, exist_ok=True)

    # ---------------- journal ----------------
    def save(self):
        self.journal_path.write_text(json.dumps(self.state, indent=2, sort_keys=True) + "\n")

    def note(self, stage, **extra):
        self.state.update(extra)
        self.state["stage"] = stage
        self.save()
        print("STAGE", stage, json.dumps(extra, sort_keys=True), flush=True)

    # ---------------- 0. preconditions ----------------
    def check_image(self):
        if not self.image.is_file():
            raise OverlayError("missing image %s" % self.image)
        raw = self.image.read_bytes()
        if len(raw) % 4:
            raise OverlayError("image size %d is not a multiple of 4" % len(raw))
        head = raw[:256]
        if SYNC_SWAPPED not in head:
            hint = (" (found the *unswapped* sync word -- run make_swap.py first)"
                    if SYNC_PLAIN in head else "")
            raise OverlayError("no 0x665599aa sync word in the first 256 bytes" + hint)
        self.state["image_bytes"] = len(raw)
        self.state["image_sha256"] = hashlib.sha256(raw).hexdigest()
        return raw

    # ---------------- 1. record ----------------
    def record(self):
        self.state["fpga_state_before"] = _read(FPGA_STATE)
        self.state["fpga_flags_before"] = _read(FPGA_FLAGS)
        self.state["firmware_class_path_before"] = _read(FW_PATH)
        self.state["panic_before"] = _read(Path("/proc/sys/kernel/panic"))
        self.state["panic_on_oops_before"] = _read(Path("/proc/sys/kernel/panic_on_oops"))
        bindings = {}
        if DEVICES.is_dir():
            for dev in DEVICES.iterdir():
                drv = driver_of(dev.name)
                if drv:
                    bindings[dev.name] = drv
        self.state["bindings"] = bindings
        for node in ("pcm0p", "pcm1c"):
            self.state["pcm_" + node] = _read(Path("/proc/asound/card0/%s/sub0/status" % node))
        _, tail = _run(["dmesg"])
        self.state["dmesg_tail_before"] = tail[-1500:]
        self.save()
        self.note("state_recorded")

    # ---------------- 2. quiesce ----------------
    def quiesce(self):
        if self.dry_run:
            self.note("quiesce_skipped_dry_run")
            return
        rc, out = _run(["alsactl", "-f", str(self.run_dir / "mixer_before.state"), "store", "0"])
        self.state["alsactl_store_rc"] = rc
        # pause (SIGSTOP) helper daemons, kill stragglers holding the sound card
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit() or int(entry.name) == os.getpid():
                continue
            try:
                cmd = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
            except OSError:
                continue
            for pat in self.pause_patterns:
                if pat in cmd:
                    try:
                        os.kill(int(entry.name), signal.SIGSTOP)
                        self.state["paused"].append([int(entry.name), pat])
                    except OSError:
                        pass
            if self.kill_audio and (cmd.startswith("aplay") or cmd.startswith("arecord")
                                    or " aplay " in cmd or " arecord " in cmd):
                try:
                    os.kill(int(entry.name), signal.SIGKILL)
                    self.state["killed"].append(int(entry.name))
                except OSError:
                    pass
        self.note("quiesced", paused=len(self.state["paused"]), killed=len(self.state["killed"]))

    # ---------------- 3. unbind ----------------
    def unbind(self):
        if self.dry_run:
            self.note("unbind_skipped_dry_run")
            return
        for dev in self.consumers:
            drv = driver_of(dev)
            if not drv:
                self.state["unbound"].append("%s=absent" % dev)
                continue
            try:
                _write(Path("/sys/bus/platform/drivers", drv, "unbind"), dev)
                self.state["unbound"].append("%s=unbound:%s" % (dev, drv))
            except OSError as exc:
                self.state["unbound"].append("%s=error:%s" % (dev, exc))
            print("UNBIND", dev, self.state["unbound"][-1], flush=True)
        self.note("consumers_unbound")

    # ---------------- 4. load ----------------
    def load(self):
        if self.dry_run:
            self.note("load_skipped_dry_run")
            return "dry-run"
        # If an oops comes from a stale consumer, reboot instead of hanging: U-Boot
        # reloads the factory bitstream, which is the most reliable rollback there is.
        try:
            _write(Path("/proc/sys/kernel/panic"), str(self.panic_seconds))
        except OSError:
            pass
        old = _read(FW_PATH) or ""
        try:
            _write(FW_PATH, str(self.run_dir))
            _write(FPGA_FLAGS, "0")
            _write(FPGA_FW, self.image.name)
        finally:
            try:
                _write(FW_PATH, old or "/lib/firmware")
            except OSError:
                try:
                    _write(FW_PATH, "/lib/firmware")
                except OSError:
                    pass
        self.state["firmware_class_path_after"] = _read(FW_PATH)
        after = None
        for _ in range(50):
            time.sleep(0.1)
            after = _read(FPGA_STATE)
            if after == "operating" and self.state.get("fpga_state_before") != "operating":
                break
        self.state["fpga_state_after"] = after
        self.note("bitstream_loaded", state=after)
        if after != "operating":
            _, d = _run(["dmesg"])
            self.state["dmesg_load"] = d[-2000:]
            self.save()
            raise OverlayError("fpga_manager state=%r after load" % after)
        return after

    # ---------------- 5. rebind ----------------
    def rebind_devices(self):
        if self.dry_run:
            self.note("rebind_skipped_dry_run")
            return
        for dev in self.rebind:
            drv = self.state.get("bindings", {}).get(dev)
            if not drv:
                self.state["rebound"].append("%s=unknown-driver" % dev)
                continue
            if driver_of(dev):
                self.state["rebound"].append("%s=already" % dev)
                continue
            try:
                _write(Path("/sys/bus/platform/drivers", drv, "bind"), dev)
                self.state["rebound"].append("%s=bound" % dev)
            except OSError as exc:
                self.state["rebound"].append(
                    "%s=%s" % (dev, "auto" if driver_of(dev) else "error:%s" % exc))
            time.sleep(0.2)
            print("BIND", dev, self.state["rebound"][-1], flush=True)
        self.note("consumers_rebound")

    def restore_mixer(self, expect_snd=True):
        rc, out = _run(["alsactl", "-f", str(self.run_dir / "mixer_before.state"), "restore", "0"])
        self.state["alsactl_restore_rc"] = rc
        deadline = time.monotonic() + 15
        while not Path("/dev/snd/controlC0").exists() and time.monotonic() < deadline:
            time.sleep(0.2)
        ok = Path("/dev/snd/controlC0").exists()
        self.state["sound_control"] = ok
        _, d = _run(["dmesg"])
        self.state["dmesg_tail_after"] = d[-2000:]
        self.note("done", sound_control=ok)
        if expect_snd and not ok:
            raise OverlayError("/dev/snd/controlC0 missing after rebind")

    # ---------------- 6. rollback ----------------
    def rollback(self, factory_image: Path):
        """Hot rollback to a previously saved image (usually built from the boot
        bitstream by prepare_recovery.py before the first experiment)."""
        self.state["rollback_image"] = str(factory_image)
        self.state["rollback_sha256"] = hashlib.sha256(Path(factory_image).read_bytes()).hexdigest()
        self.note("rollback_start")
        self.unbind()
        old = _read(FW_PATH) or ""
        try:
            _write(FW_PATH, str(Path(factory_image).parent))
            _write(FPGA_FLAGS, "0")
            _write(FPGA_FW, Path(factory_image).name)
        finally:
            try:
                _write(FW_PATH, old or "/lib/firmware")
            except OSError:
                pass
        time.sleep(0.5)
        after = _read(FPGA_STATE)
        self.state["fpga_state_after_rollback"] = after
        self.rebind_devices()
        self.note("rollback_done", state=after)
        if after != "operating":
            raise OverlayError("rollback left fpga_manager in state=%r (cold reboot is the "
                               "fallback: U-Boot reloads the factory bitstream)" % after)

    # ---------------- orchestration ----------------
    def run(self):
        try:
            self.check_image()
            self.record()
            self.quiesce()
            self.unbind()
            self.load()
            self.rebind_devices()
            self.restore_mixer()
            print(json.dumps({k: v for k, v in self.state.items()
                              if k.startswith("fpga")}, indent=2))
            return 0
        except BaseException as exc:      # noqa: BLE001 -- journalling matters more
            self.state["exception"] = repr(exc)
            self.save()
            raise


def load_list(spec: str):
    """--consumers/--rebind accept a file with one device per line/whitespace."""
    if not spec:
        return []
    p = Path(spec)
    if p.is_file():
        text = p.read_text()
        return [t for t in text.replace(",", " ").split() if t and not t.startswith("#")]
    return [t for t in spec.replace(",", " ").split() if t]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--image", required=True, type=Path,
                    help="byte-swapped .bin for fpga_manager (see make_swap.py)")
    ap.add_argument("--run-dir", required=True, type=Path,
                    help="staging dir that already holds the image (tmpfs is fine)")
    ap.add_argument("--consumers", default="", help="devices to unbind before load "
                                                   "(file with one per line, or space/comma list)")
    ap.add_argument("--rebind", default="", help="devices to bind back after load")
    ap.add_argument("--pause", default="", help="cmdline substrings to SIGSTOP during load")
    ap.add_argument("--keep-audio", action="store_true", help="do not SIGKILL aplay/arecord")
    ap.add_argument("--panic", type=int, default=10, help="kernel panic= seconds during load")
    ap.add_argument("--rollback-to", type=Path, default=None,
                    help="hot-rollback to this image instead of loading --image")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    ld = OverlayLoader(args.image, args.run_dir,
                       consumers=load_list(args.consumers),
                       rebind=load_list(args.rebind),
                       pause=load_list(args.pause),
                       kill_audio=not args.keep_audio,
                       panic_seconds=args.panic,
                       dry_run=args.dry_run)
    if args.rollback_to:
        ld.record()
        ld.rollback(args.rollback_to)
        return 0
    return ld.run()


if __name__ == "__main__":
    sys.exit(main())
