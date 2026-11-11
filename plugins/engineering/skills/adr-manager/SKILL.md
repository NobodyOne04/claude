---
name: adr-manager
description: Create, review, update and supersede Architecture Decision Records (ADRs), never approving one myself. Use when I ask about ADRs, when an architectural decision with long-term consequences is discussed or approved (suggest recording it), when an existing ADR must be updated, deprecated or superseded, or when a project needs an ADR folder.
---

# ADR manager

ADRs record decisions **I** approved: context, alternatives, rationale, consequences.
Claude drafts and maintains them; Claude never approves or finalizes one.

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
# NNNN. <Title>

- Status: Proposed | Accepted | Rejected | Deprecated | Superseded by [NNNN](NNNN-....adr)
- Date: YYYY-MM-DD
- Supersedes: [NNNN](NNNN-....adr)   <!-- only if it does -->

## Context
<problem, requirements, constraints>

## Decision
<the chosen approach>

## Alternatives
<other options considered and why not>

## Rationale
<why this one>

## Consequences
<positive and negative>

## References
<docs, discussions, related ADRs>
```
Required: title, status, date, context, decision, consequences. Keep it short but enough
for a future developer to understand why.

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
- **New ADR**: id and title, context, alternatives, proposed decision, rationale and
  consequences, approval status.
- **Review**: current statuses, inconsistencies, outdated or conflicting decisions,
  recommended actions.
- **Supersession**: previous decision, reason, new decision, links between them.

## Not this skill's job
Making or approving decisions, implementing them, architecture audits (`architecture-review`),
security audits (`security-audit`).
