---
name: codex
description: Talk to OpenAI Codex, my read-only second agent, through its CLI. Use whenever you call Codex for a review, an audit, a second opinion or docs, when I say "ask Codex", "have Codex review/check/write", or when another skill tells you to bring in Codex.
---

# Codex: read-only second agent

Decision: ADR 0006 in my `claude` repo.

## Roles
- **Me**: design decisions and ADR approvals.
- **You (Claude)**: the only agent that writes code.
- **Codex**: reviews, audits, writes docs. **Never edits code.** Its findings come back to
  you; you verify each one and make the fixes yourself.

## Before the first call
Check `codex login status`. Not installed or not logged in: tell me, carry on without
Codex, and say it was skipped. Codex never blocks work.

## Commands
Run them from the repo root, through Bash.

| Need | Command |
|---|---|
| Ask something (new thread) | `codex exec -s read-only --json "<prompt>"`, keep the `thread_id` of the first event |
| Continue that thread, with its context | `codex exec resume <thread_id> -c sandbox_mode="read-only" "<prompt>"` |
| Review the branch | `codex review --base main` |
| Write docs | `codex exec -s workspace-write --worktree "<prompt>"` |

- `resume` has no `-s` flag: always pass `-c sandbox_mode="read-only"`, or the thread runs
  with the default sandbox.
- Never use `--dangerously-bypass-approvals-and-sandbox`, `workspace-write` outside the
  docs case, or `danger-full-access`.
- With `--json`, read the agent's final message from the events; don't paste raw JSONL to me.
- Prompts: say what to look at, that it's read-only, and the answer shape you want
  ("list findings as `file:line: problem`; say 'nothing found' if none").

## Docs
- Codex writes in its own worktree. Check its diff before taking anything: only `*.md` or
  files under `docs/`, never ADR files (`*.adr`: those stay with you and me), never code.
  Anything else in the diff: reject the whole diff and tell me.
- You commit the accepted docs and open the PR (`github-flow`, `commit-style`). Codex never
  commits or pushes.

## Showing me the exchange
- I want to see the conversation: quote each Codex reply to me **in full** (as a block
  quote), then what you make of it. Don't replace it with a summary.
- For every finding say what you did: fixed (how), or dismissed (why).
- Codex is a second opinion, not an authority: verify a finding in the code before acting.
