---
name: vivado-mcp-git-collaboration
description: Use this skill for Vivado/Vitis work through the repository's Vivado MCP client and for task-scoped Git/GitHub changes in this FPGA project. It captures verified Windows/WSL invocation details and lessons from recent PS/PL rounds.
---

# Vivado MCP and Git Collaboration

Use this skill when a task touches Vivado/Vitis through MCP, FPGA build evidence, or a task branch/commit/PR in this repository. The root `AGENTS.md`, current `coummucation.md`, and the task's ownership rules remain authoritative; this skill explains how to apply them in the workflows that have failed before.

Before acting, inspect the worktree and open PRs. Do not carry unrelated or user-owned changes into a task commit. Claim the task in `coummucation.md` before changing shared project files.

Read only the reference needed for the current work:

- [Vivado MCP](references/vivado_mcp.md) for server/session use, Tcl calls, and tool failures.
- [Git and GitHub](references/git_github.md) for branch, claim, commit, push, and PR handling.
- [Round lessons](references/round_lessons.md) for verified failures and acceptance boundaries from recent PS/PL rounds.

Keep evidence scoped to what was actually tested. A successful Tcl command, C-sim, OOC implementation, board boot, running PL counter, audio process, or user listening result proves different things; do not combine them into a stronger claim than the evidence supports.
