# Round Lessons

These findings come from repository reports, especially `PL-20261027-01` Rounds 17-34 and the 2026-10-17 Vivado MCP setup report. Treat them as failure patterns and evidence boundaries, not guarantees that every later build has the same cause.

## Vivado and HLS

- **Wrong executable path:** Vivado 2026.1 was installed one directory deeper than first assumed. Verify the executable path and run `version -short` through MCP before starting a project.
- **Empty device registry:** MCP was healthy while Vivado had no registered parts. Verify `get_parts` in the active session; repair/install the Zynq-7000 device files and restart the session before blaming Tcl or RTL.
- **Simulation workspace:** xsim failed under the workspace file-filter driver but passed outside the workspace. Keep an external scratch simulation directory available and preserve source/testbench hashes.
- **Long generated paths:** HLS `generate_target` failed under a long Windows path, then passed with identical sources in a short external project root. Treat path depth as a tool constraint and document the successful root.
- **MCP long-script hangs:** Long commands through a webserver fallback were unreliable. Keep the persistent build in Tcl files, issue short diagnostic calls, and inspect the command/session logs.
- **Transform scaling contract (Rounds 32-33):** A host hook applied `/1024` a second time after HLS IFFT had already normalized. It produced SNR near 0.1 dB and errors above 17,000 PCM16 counts; removing only that duplicate scaling yielded >104 dB and one-count errors. Write down normalization at each interface and retain a one-variable A/B regression.

## Integration and board evidence

- **OOC is not full-system signoff:** Round17 kernel OOC timing passed, but Round18 full Zynq integration still had to check PS, AXI, audio, routing, resources, and system timing. Round18 then passed its stated routed internal timing gates, while external audio I/O delays remained incomplete.
- **Numerical correctness is not live audio:** Round20 passed 24 vectors and two real files with about 97 dB SNR and max one PCM16 count error, but did not record/play audio. Round21 had zero xrun and active PL calls but was rejected when the operator heard no sound; Round23 passed only after a fresh prompt/readiness confirmation and explicit audible feedback.
- **No speech means no speech stability result:** Round24 ran 60 seconds without xrun but contained zero voiced frames and was rejected for the intended stability gate. Do not count silence or a process exit code as a valid speech run.
- **Boot races require owner-specific cleanup:** Round29 candidate startup raced with `music-button` leaving a detached factory `aplay` holding the playback PCM. Round30 fixed this by stopping that service, terminating only the specifically identified test player, waiting for PCM closure, clearing stale PID/state before daemon launch, and atomically replacing state. Do not generalize this into a global `killall`.
- **Persistent boot is a deployment result, not total acceptance:** Round30 verified a normal reboot selected `WORLD minphase PL candidate`, `READY_CANDIDATE`, active capture/playback, and increasing PL call counts. The report explicitly waived long stability and prompt audibility and limits the claim to the fused minimum-phase stage, not all of WORLD.
- **Kernel/OOC resource wins need a measured system comparison:** A small kernel-level timing win may be hidden by DMA copies, ioctl, packing, scheduling, or audio I/O. Measure CPU and PL paths on identical inputs and binaries; report whole-pipeline wall time/RTF and overhead separately.
- **Do not alter the live system to improve a report:** persistent installation, boot configuration, FPGA switching, audio routing, and user audio tests are separate operations. Follow the current owner/claim and readiness rules; preserve factory hashes and recovery evidence where deployment is in scope.

## Round discipline

- Change one material variable per round and freeze input hashes, binary/model hashes, tool versions, constraints, and the acceptance threshold.
- Keep rejection evidence. A failed round should identify the trigger, measured failure, root cause if established, and the single next change; do not bury it under a later pass.
- Separate proof levels in both JSON and prose: host model/C-sim, RTL cosim, OOC route, full-design route, board numerical comparison, live I/O, user listening, and stability.
- Preserve contradictory observations. A later pass may supersede a state, but does not erase the earlier log or make a previous failure false.
