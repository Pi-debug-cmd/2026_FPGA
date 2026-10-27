#!/usr/bin/env python3
"""Register-map driven acceptance check for a PL overlay (AXI-Lite / AXI-GPIO).

The register map is DATA (`register_map.json`), so this file never changes when
the overlay changes: point it at another map and it checks that overlay.

Checks performed per register
-----------------------------
1. reset   : value read right after load matches the documented reset value
             (proves the BD elaboration-time constant / C_DOUT_DEFAULT is live,
              and that nothing else wrote the block before us)
2. rw      : every value in `test` is written and read back through `mask`
3. mirror  : values are restored to `restore` (default: the reset value) at the end
4. side-effect free: read-only registers are only read

Exit code 0 only if all checks pass; the JSON on stdout is the machine-readable
evidence that goes into the submission.

Two implementations are shipped on purpose:
  * regtool.py  -- this file, needs a Python with the `mmap` module
  * regtool.c   -- static C, for stripped PetaLinux images whose python3 has no
                   mmap module (that is exactly what we hit on the board)
"""
from __future__ import annotations

import argparse
import json
import mmap
import os
import struct
import sys


class Mapper:
    def __init__(self, page: int = 4096):
        self.fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        self.page = page
        self._maps = {}

    def window(self, phys: int):
        base = phys & ~(self.page - 1)
        if base not in self._maps:
            self._maps[base] = mmap.mmap(self.fd, self.page,
                                         mmap.MAP_SHARED,
                                         mmap.PROT_READ | mmap.PROT_WRITE,
                                         offset=base)
        return self._maps[base], phys - base

    def rd(self, phys: int) -> int:
        m, off = self.window(phys)
        return struct.unpack_from("<I", m, off)[0]

    def wr(self, phys: int, val: int) -> None:
        m, off = self.window(phys)
        struct.pack_into("<I", m, off, val & 0xFFFFFFFF)


def mask_of(reg: dict) -> int:
    w = int(reg.get("width", 32))
    return 0xFFFFFFFF if w >= 32 else (1 << w) - 1


def check_register(mp: Mapper, base: int, reg: dict, results: list, restore: bool):
    addr = base + int(str(reg.get("offset", "0x0")), 0)
    msk = mask_of(reg)
    name = reg["name"]
    rec = {"name": name, "addr": "0x%08x" % addr, "width": int(reg.get("width", 32)),
           "mask": "0x%x" % msk, "cases": []}

    initial = mp.rd(addr) & msk
    rec["initial"] = initial
    if "reset" in reg:
        rec["reset_expected"] = reg["reset"]
        rec["reset_ok"] = (initial == (reg["reset"] & msk))
        if not rec["reset_ok"]:
            rec["diagnosis"] = ("reset mismatch: BD constant / C_DOUT_DEFAULT not applied, "
                                "or the block was already written -- do NOT trust later "
                                "readback comparisons until this is explained")
    if reg.get("access", "rw") == "ro":
        results.append(rec)
        return

    for val in reg.get("test", []):
        val &= msk
        mp.wr(addr, val)
        got = mp.rd(addr) & msk
        rec["cases"].append({"wrote": val, "read": got, "ok": got == val})
    rec["rw_ok"] = all(c["ok"] for c in rec["cases"])

    if restore:
        mp.wr(addr, reg.get("restore", reg.get("reset", 0)))
        rec["restored"] = mp.rd(addr) & msk
        rec["restored_ok"] = rec["restored"] == (reg.get("restore", reg.get("reset", 0)) & msk)
    results.append(rec)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("map_json", help="register map (see example/register_map.json)")
    ap.add_argument("--block", default=None, help="only this block name")
    ap.add_argument("--no-restore", action="store_true",
                    help="leave registers as-is (default restores reset values)")
    ap.add_argument("--json", default=None, help="also write this JSON file")
    args = ap.parse_args(argv)

    spec = json.loads(open(args.map_json, encoding="utf-8").read())
    mp = Mapper()
    out = {"device": spec.get("device", "?"), "map": args.map_json, "blocks": []}
    all_ok = True
    for blk in spec["blocks"]:
        if args.block and blk["name"] != args.block:
            continue
        base = int(str(blk["base"]), 0)
        rec = {"name": blk["name"], "base": "0x%08x" % base, "registers": []}
        for reg in blk["regs"]:
            check_register(mp, base, reg, rec["registers"], not args.no_restore)
        rec["ok"] = all(r.get("rw_ok", True) and r.get("reset_ok", True) and
                        r.get("restored_ok", True) for r in rec["registers"])
        all_ok &= rec["ok"]
        out["blocks"].append(rec)
    out["all_ok"] = all_ok

    text = json.dumps(out, indent=2, sort_keys=True)
    print(text)
    if args.json:
        open(args.json, "w", encoding="utf-8").write(text + "\n")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
