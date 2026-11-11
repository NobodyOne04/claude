# 0003. Only the owner merges to main, enforced by a hook

- Status: Proposed
- Date: 2026-11-11

> Records an existing decision; not yet approved by the owner.

## Context
Claude works through branches and PRs in all my repos. A merge or push to `main` by Claude
would skip my review.

## Decision
The `workflow` plugin ships a `PreToolUse` hook (`guard-main.py`) that blocks PR merges and
pushes to `main`. Changes go through a branch and PR (`github-flow`), and I merge.

## Alternatives
- Instructions only: a model can still run the command.
- GitHub branch protection alone: doesn't cover local repos or repos without it set up.

## Rationale
A hard local block works in every repo, regardless of remote settings.

## Consequences
- Positive: nothing reaches `main` without me.
- Negative: chained commands with `git push` are refused; push runs on its own.

## References
`plugins/workflow/hooks/guard-main.py`, `test-guard.sh`, `github-flow` skill.
