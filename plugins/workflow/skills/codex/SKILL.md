---
name: codex
description: Talk to OpenAI Codex, my read-only second agent, through its CLI. Use whenever you call Codex for a review, an audit, a second opinion or docs, when I say "ask Codex", "have Codex review/check/write", or when another skill tells you to bring in Codex.
---

# Codex: read-only second agent

Decisions: ADRs 0006-0009 in my `claude` repo.

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

## Commands
Every call goes through the launcher next to this file (ADR 0008). It sets the sandbox,
approval policy, MCP and connector flags itself, checks `codex login status`, and works from
any directory. Never call `codex` directly. No Codex call can write: docs come back as text
(ADR 0009).

| Need | Command |
|---|---|
| Ask something (new thread) | `python3 -I <this skill's dir>/codex.py ask --repo <repo root>` |
| Continue that thread | `python3 -I <this skill's dir>/codex.py resume <thread_id> --repo <repo root>` |
| Review the branch | from the repo root: `python3 -I <this skill's dir>/codex.py review` (`--base REF`, default `origin/main`) |
| Propose docs | `python3 -I <this skill's dir>/codex.py docs --repo <repo root>` |
| Apply them | `python3 -I <this skill's dir>/codex.py docs-apply --repo <repo root> --sha256 <hex> <patch>` |

- The prompt goes on stdin, as a quoted heredoc with this exact delimiter, which never
  appears inside a prompt:
  ```
  python3 -I <dir>/codex.py ask --repo . <<'CODEX_PROMPT_END'
  <prompt>
  CODEX_PROMPT_END
  ```
- `--repo`: the repo the question is about, so Codex reads its files and `AGENTS.md`. Leave it
  out only for a question about no repo.
- Output: `thread: <id>` (keep it for `resume`) or `Codex review of <base>..<head>`, then
  Codex's final message. Copy the review header line into `## Codex review`.
- Exit 3 prints only `Codex: skipped (<reason>)`: Codex was unavailable or the call failed.
  Write that line where the result would have gone and carry on. Codex never blocks work.
- Exit 4 prints `Codex: rerun (<reason>)`: the review would not match the branch (uncommitted
  changes, or the branch changed meanwhile). Not a skip: do what it says and run the review
  again; never push on it.
- Prompts: say what to look at, that it's read-only, and the answer shape you want
  ("list findings as `file:line: problem`; say 'nothing found' if none").

## Docs
- `docs` sends the task to a read-only Codex, which replies with each file's full new text.
  The launcher checks every path (only `.md`; never `docs/adr/`, `SKILL.md`, `CLAUDE.md`,
  `AGENTS.md`, dot directories, symlinks, executables or untracked files) and builds the diff
  itself. Nothing is written yet.
- Output: `repo:`, `patch:`, `sha256:`, the stat, then the full diff. Show me the full diff
  (the redaction rule below applies), then run `docs-apply` with that patch and SHA-256: it
  refuses a changed patch, re-checks the paths, applies, and deletes the patch.
- Exit 2, `Codex docs: rejected, nothing written`, then one line per reason: tell me, and fix
  the prompt or write those files yourself. `SKILL.md`, `CLAUDE.md` and `AGENTS.md` are always
  yours to write.
- Review the applied text like your own, then commit and open the PR (`github-flow`,
  `commit-style`). Codex never commits or pushes.

## Showing me the exchange
- I want to see the conversation: quote each Codex reply to me **in full** (as a block
  quote), then what you make of it. Don't replace it with a summary. Only exception:
  redact secrets, tokens and personal data, and say you did. The same goes for everything
  of Codex's you write elsewhere (PR body, Security Report): location and a redacted
  description, never the value.
- For every finding say what you did: fixed (how), or dismissed (why).
- Codex is a second opinion, not an authority: verify a finding in the code before acting.
