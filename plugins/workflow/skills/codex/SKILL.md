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

## When: every time, not when it seems useful (ADR 0007)
| Trigger | What Codex does | Where the result goes |
|---|---|---|
| Every PR, before the first push (`github-flow`) | `codex review` of the branch | `## Codex review` in the PR body |
| Every ADR draft, before I see it (`adr-manager`) | critiques the draft | your message to me: points taken, points rejected with why |
| Every bug fix (`bug/`, `hotfix/`), before you fix | its own root-cause analysis | PR body: where you and Codex agreed or differed |
| Every security audit, once I've asked for one (`security-audit`) | independent read-only audit | the Security Report, confirmed findings marked `found by: Codex` |

The only skip: Codex unavailable (not installed, not logged in, the call fails). Then write
`Codex: skipped (<reason>)` where the result would have gone. Never skip because a change
looks small.

## Before the first call
Check `codex login status`. Not installed or not logged in: tell me, carry on without
Codex, and say it was skipped. Codex never blocks work.

## Commands
Run them through Bash. Ask and continue work from any directory; review and docs need a git
repo, so run those from its root.

| Need | Command |
|---|---|
| Ask something (new thread) | `codex exec --skip-git-repo-check -s read-only -c approval_policy="never" --json "<prompt>"`, keep the `thread_id` of the first event |
| Continue that thread, with its context | `codex exec resume --skip-git-repo-check -c sandbox_mode="read-only" -c approval_policy="never" <thread_id> "<prompt>"` |
| Review the branch | `git fetch origin main`, then `codex review --base origin/main -c sandbox_mode="read-only" -c approval_policy="never"` |
| Write docs | `codex exec -s workspace-write -c approval_policy="never" --worktree "<prompt>"` |

- Always pass `-c approval_policy="never"`. My config lets Codex ask to escalate and has
  its auto-reviewer approve, which runs the command **outside the sandbox**: with
  `-s read-only` alone, a `touch` still wrote a file (2026-11-25).
- `resume` and `review` have no `-s` flag: always pass `-c sandbox_mode="read-only"`, or
  they run with the default sandbox (my config doesn't default to read-only).
- `--skip-git-repo-check` lets Codex start outside a git repo. It grants nothing: the sandbox
  and approval policy above still apply.
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
  quote), then what you make of it. Don't replace it with a summary. Only exception:
  redact secrets, tokens and personal data, and say you did. The same goes for everything
  of Codex's you write elsewhere (PR body, Security Report): location and a redacted
  description, never the value.
- For every finding say what you did: fixed (how), or dismissed (why).
- Codex is a second opinion, not an authority: verify a finding in the code before acting.
