# Vivado MCP

## Use the repository client

The project client is `tools/mcp_vivado.py`, implemented with Python's standard library. It starts the MCP daemon if needed and exposes the operations below:

```powershell
python tools/mcp_vivado.py status
python tools/mcp_vivado.py start
python tools/mcp_vivado.py exec "puts [version -short]"
python tools/mcp_vivado.py raw vivado_execute '{"session_id":"<session-id>","command":"puts [version -short]"}'
python tools/mcp_vivado.py stop <session-id>
```

`status` lists sessions and may start the daemon. `start` creates a Tcl-mode Vivado session. `exec` is a convenience wrapper that selects the first matching Vivado session; use `raw vivado_execute` with an explicit session ID if several sessions are active or ownership matters. Stop only the session created for this task. Do not use daemon-wide `--kill-all` against a shared environment.

At session start, verify the version, device, and project context before a build:

```powershell
python tools/mcp_vivado.py exec "puts [version -short]"
python tools/mcp_vivado.py exec "puts PARTS=[llength [get_parts xc7z020clg400-2]]"
```

The project's verified setup uses Vivado 2026.1 and `xc7z020clg400-2`. Resolve the active installation locally; the historical Windows path `D:\USER_Software\vivado\2026.1\Vivado\bin\vivado.bat` is machine-specific. The extra `Vivado` directory level matters on that host. A `Vivado binary not found` response is a path/configuration problem until independently disproven.

## Tcl and build handling

- Keep Tcl expressions simple and avoid wrapping bracket substitutions in an extra Tcl double-quoted string. For example, use `puts N=[llength [get_parts]]` instead of `puts "N=[llength [get_parts]]"`.
- Use the project's Tcl scripts for repeatable builds. A long Tcl body sent through an MCP/webserver fallback has hung before; split interactive diagnosis into short commands and use a checked-in Tcl script for the reproducible build.
- Record the session ID, tool version, part, clock constraint, source revision, command/script, output paths, and relevant reports. Check tool-reported errors and generated reports, not just the client process exit code.
- Confirm the requested part exists in the active session. A broken/incomplete device installation produced zero parts and `Could not get a valid part`; restarting a Vivado session after repairing device data was necessary because old sessions cached the empty registry.
- When HLS/IP generation hits Windows path-length failures, use a short task-specific build root such as `D:/wpl_<date>_<round>/...`; do not move or overwrite the checked-in sources. Record that external build path and all source/testbench/script hashes so another engineer can reproduce it.
- In this project environment, xsim has crashed under the workspace file filter. Put simulation work products under an approved external scratch path (historically `D:/xsim_work/<task>`), while keeping source vectors and reproduction commands in the repository. Recheck current machine policy before assuming the historical workaround is still needed.
- Check license availability before synthesis/implementation. Version queries and basic Tcl expressions do not prove that a synthesis license or device installation is usable.

## Failure triage

1. Save the exact request, response, session ID, and relevant MCP/Vivado log.
2. Separate client/server/session errors from Vivado command errors and installation/license errors.
3. Run the smallest diagnostic in the same session (`version`, `get_parts`, then a minimal read/synth/sim check as appropriate).
4. Change one cause at a time. Preserve failed logs and record the resolution in the same task round.
5. If a session is shared or its owner is unclear, inspect/list sessions and coordinate; do not stop or reset it speculatively.

## Evidence boundary

RTL simulation establishes behavior against its testbench. OOC implementation establishes kernel-level implementation only. A full block design and routed top-level establish system integration/timing under the stated constraints. A loaded bitstream or active `fpga_manager` does not establish that the intended accelerator is being called. Board counters, data comparisons, live audio, user listening, and long-duration stability each require their own evidence.
