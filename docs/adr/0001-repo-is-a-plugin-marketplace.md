# 0001. The setup repo is a Claude Code plugin marketplace

- Status: Accepted
- Date: 2026-11-11

> Records an existing decision. Accepted by the owner on 2026-11-11.

## Context
The same skills, hooks and MCP servers must work on the Mac and on Arch, and stay in sync.

## Decision
The repo is a plugin marketplace (`nobodyone`, `.claude-plugin/marketplace.json`) with one
plugin per area under `plugins/`. Machines add it from the local clone and install with
`make setup`. A plugin only updates when its `plugin.json` `version` changes, so every PR bumps
the version of each plugin it touches. The clone stays on `main`: the local marketplace
installs whatever is checked out.

## Alternatives
- Symlink or copy files into `~/.claude`: no versioning, per-machine drift.
- One big plugin: every change reinstalls everything.

## Rationale
Uses the native install/update path; per-plugin versions make updates explicit.

## Consequences
- Positive: one command per machine, history and review through PRs.
- Negative: forgetting a version bump means the change never installs; a clone left on a
  branch installs unmerged work (warned by `marketplace-branch.py`).

## References
`README.md`, `CLAUDE.md`, `Makefile`.
