---
name: adr-manager
description: Create, review, update and supersede Architecture Decision Records (ADRs), never approving one myself. Use before writing code for any feature or major change in a project (the ADR comes first), when I ask about ADRs, when an architectural decision with long-term consequences is discussed or approved (suggest recording it), when an existing ADR must be updated, deprecated or superseded, or when a project needs an ADR folder.
---

# ADR manager

ADRs record decisions **I** approved: context, alternatives, rationale, consequences.
Claude drafts and maintains them; Claude never approves or finalizes one.

## ADR first, then code
In any project with a codebase:
- Every feature or major change starts with an ADR. Write no code, scaffolding or config for
  it until I approve the ADR (`Accepted`) and give the go. Show me the draft and stop.
- Granular: one decision per ADR. A feature that needs several decisions gets several ADRs.
- Dependencies set the order: if B depends on A, A gets the lower number and is implemented
  first.
- One ADR, one PR: the PR carries the ADR and its implementation, nothing else (`github-flow`).
- Minor changes (fix, docs, tweak) need no new ADR; they use the latest ADR's minor number
  (`commit-style`).

## Rules
- Read existing ADRs before proposing a decision; avoid duplicates, link related ones.
- An ADR becomes `Accepted` only after my explicit approval. Never present a proposal as
  an established decision.
- Never silently rewrite or delete an accepted ADR. Changes to one are discussed with me first.
- Never record assumptions as confirmed decisions.
- If an accepted ADR contradicts the implementation, report the discrepancy; don't edit the
  record to match.
- Suggest an ADR when a decision has long-term architectural consequences, even unasked.
  Minor implementation details don't get one.

## Where
- Default `docs/adr/NNNN-short-title.adr` (`0001-use-postgresql.adr`): sequential four-digit
  numbers, never reused. Markdown content, but always the `.adr` extension (not `.md`), so
  ADRs are told apart from other docs; the folder's index stays `README.md`.
- If the project already has an ADR convention (folder, numbering, template), follow it,
  except the extension: ADRs found as `.md` get renamed to `.adr` (links included), with my OK.
- Check the highest existing number before creating a new one.

## Template
```markdown
# NNNN. <Short title>

- Status: Proposed | Accepted | Rejected | Deprecated | Superseded by [NNNN](NNNN-....adr)
- Date: YYYY-MM-DD
- Supersedes: [NNNN](NNNN-....adr)   <!-- only if it does -->

<Purpose: one or two sentences, what this ADR decides and why it exists.>

## Technical details
<Rich and concrete: the problem and constraints, the decision, how it works (files,
commands, config keys, data flow, edge cases), why this approach, and its consequences
(positive and negative). Name real paths, commands and values; use bullets or sub-headings
when it gets long.>

## Technologies and alternatives
- Involved: <libraries, tools, services and versions it relies on>
- Alternatives: <option: why not>, one line each
```
- Title: short. Purpose: brief, no details there.
- **Technical details** is the body: enough for a future developer to rebuild the decision
  and its implementation without reading the code first.
- **Technologies and alternatives**: brief. Drop a line with nothing to say; drop the whole
  section if both are empty.
- Related ADRs and references are linked inline where they matter.

## Statuses
- **Proposed**: under consideration; says plainly it's not approved.
- **Accepted**: I approved it; text matches what was actually agreed.
- **Rejected**: I rejected it; keep it when the history is useful, with the reason.
- **Deprecated**: no longer applies, nothing replaces it.
- **Superseded**: replaced by a newer accepted ADR; both link to each other.

## Workflows
**Create**: confirm it's architecturally significant → read related ADRs → draft from the
template → show me → on explicit approval set `Accepted` and save. If I want the draft kept
before deciding, save it as `Proposed`.

**Review**: check ADRs against the current code; report outdated, conflicting or
differently-implemented decisions and ones worth reconsidering; recommend actions. No edits
without my agreement.

**Supersede**: name the ADR being replaced and why → draft the new one → my explicit
approval → new ADR `Accepted` with `Supersedes`, old one `Superseded by`, its body untouched.

## Output
- **New ADR**: id and title, purpose, technical details, technologies and alternatives,
  approval status.
- **Review**: current statuses, inconsistencies, outdated or conflicting decisions,
  recommended actions.
- **Supersession**: previous decision, reason, new decision, links between them.

## Not this skill's job
Making or approving decisions, implementing them, architecture audits (`architecture-review`),
security audits (`security-audit`).
