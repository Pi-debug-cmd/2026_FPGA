# Git and GitHub

Follow root `AGENTS.md` and `coummucation.md` as the controlling project policy. This reference turns those rules into a task workflow.

## Before editing

```powershell
git status --short --branch
git pull --rebase origin main
gh pr list --state open --base main
```

Also check whether an open PR or another claim owns the same task/files. If the worktree is dirty and pull refuses, do not stash, reset, checkout over, or include the existing edits. Coordinate by appending to `coummucation.md`; use a clean worktree based on the current `origin/main` for an isolated task when appropriate. A local-only fetch does not replace the project requirement to reconcile with `main` before publishing.

Append a `CLAIMED` record before implementation. Include task ID, date, role, base commit, scope/paths, expected reproduction checks, known limits, and next owner. For hardware work, use the assigned task and verify no overlapping open PR; do not infer ownership from a branch name alone.

## One round per commit

Use `agent/<github-account>/<task-id>`. Keep one proposal or test round in each commit, with the task ID at the start:

```powershell
git switch -c agent/<github-account>/<task-id> origin/main
git add <only-files-for-this-round>
git diff --cached --check
git diff --cached --stat
git status --short
git commit -m "<task-id>: <result>"
```

Stage named paths rather than `git add -A` when the worktree may contain unrelated files. Every implementation/test/report round, including rejected rounds, needs a corresponding `coummucation.md` update with the exact condition, commit, measured result, evidence links, limits, and next owner. Keep prior evidence; append or minimally amend shared records rather than rewriting conclusions.

Before publishing, reconcile the branch and inspect the staged diff again:

```powershell
git fetch origin
git rebase origin/main
git diff --check origin/main...HEAD
git status --short --branch
git push -u origin agent/<github-account>/<task-id>
gh pr create --base main --head agent/<github-account>/<task-id> --title "<task-id>: <result>" --body-file <review-notes.md>
```

Use the repository's policy checker when applicable. CI requires every non-merge commit to start with the task ID and requires `coummucation.md` to change when code, test, board, proposal, or report files change. Use normal push/rebase; never force-push over another writer's work. If GitHub authentication, branch protection, or a conflict blocks publication, record the blocker and stop the publish attempt without claiming the round was published.

## Artifact boundary

Keep source, scripts, small structured evidence, and reports in their prescribed repository directories. Respect `.gitignore`: do not add Vivado caches, generated bitstreams, compiled products, model weights, or unauthorized human audio to Git history. Use the project's Release process for approved cross-computer model delivery, with per-file SHA-256 and a clean-download run; a local path or PR alone is not delivery.
