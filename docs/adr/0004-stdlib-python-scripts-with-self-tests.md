# 0004. Plugin scripts are stdlib Python with a built-in self-test

- Status: Accepted
- Date: 2026-11-11

> Records an existing decision. Accepted by the owner on 2026-11-11.

## Context
Hooks and audit scripts run on every machine, often on every tool call, with no install step.

## Decision
Scripts are Python 3, standard library only, run with `python3 -I`. Each carries its own
`--test` self-check, and `make check` (CI on every PR) runs them.

## Alternatives
- Third-party packages: need a venv per machine, widen the supply chain.
- Shell scripts: harder to parse JSON hook input and test.

## Rationale
Python is on both machines; `-I` stops planted modules from loading; self-tests keep each
script one file.

## Consequences
- Positive: zero dependencies, tested in CI.
- Negative: no libraries; tests live inside the scripts.

## References
`plugins/workflow/hooks/*.py`, `plugins/workflow/skills/plugin-audit/audit.py`, `Makefile`.
