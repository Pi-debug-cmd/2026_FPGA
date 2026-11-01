# DOCS-20261101-01 Vivado MCP and Git/GitHub Skill

## Outcome

Added a reusable skill at `skill/04_vivado_mcp_git_github/` for this repository's Vivado MCP workflow, one-round Git/GitHub collaboration, and lessons drawn from recent PS/PL work. The entrypoint keeps the selection scope narrow and links to focused references for MCP use, GitHub publication, and round-specific failure patterns. A short README explains the package contents and validation.

## Sources reviewed

- Project policy: `AGENTS.md`, `project_guide.md`, `handoff_20261021.md`, `coummucation.md`, `plan.md`, `ARTIFACTS.md`, `code_rule.md`, and `交接/远端模型交付与接收.md`.
- Vivado MCP: `tools/mcp_vivado.py` and `report/tools_vivado_mcp_20261017.md`.
- PS/PL evidence: `PL-20261027-01` reports for Rounds 17-34, including full-system implementation, board numerical comparison, live audio, persistent boot, and HLS pulse integration attempts.
- Existing contest skills: `skill/01_board_bringup/`, `skill/02_dma_coherency/`, and `skill/03_golden_compare/`.

The references preserve the evidence levels and failure outcomes from those reports; they do not convert an OOC result, process status, or boot check into a broader system/audio acceptance claim.

## Reproduction and checks

```powershell
python "C:/Users/World/.codex/skills/.system/skill-creator/scripts/quick_validate.py" skill/04_vivado_mcp_git_github
git diff --check
```

Results: Skill Creator reports `Skill is valid!`; `git diff --check` exits 0; all three reference links resolve within the skill directory. No Vivado session, FPGA build, board, audio, or GitHub mutation was used to validate the skill content.

## Limits

Examples reflect the Windows host and repository workflows recorded in the source documents. Paths, server installation, tool availability, branch ownership, and open PRs must be checked on the active machine. The skill is a procedure guide, not evidence of a fresh hardware test.

## Next

Review and merge through the repository PR process. Keep future corrections tied to new, committed evidence rather than generalizing a single failure.
