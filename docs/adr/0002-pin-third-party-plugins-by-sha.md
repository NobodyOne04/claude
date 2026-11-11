# 0002. Pin third-party plugins by commit, audit before bumping

- Status: Proposed
- Date: 2026-11-11

> Records an existing decision; not yet approved by the owner.

## Context
Plugins run code and hooks with my permissions. A third-party repo can change at any time.

## Decision
Third-party plugins listed in this marketplace (`ponytail`, `diagram-design`) are pinned by
`sha`. A bump happens only after `plugin-audit` on the new commit.

## Alternatives
- Track the default branch: upstream changes arrive unreviewed.
- Vendor a copy: manual syncing, loses upstream history.

## Rationale
Updates become deliberate and reviewed, with no copy to maintain.

## Consequences
- Positive: no silent supply-chain changes.
- Negative: upstream fixes wait for a manual bump.

## References
`.claude-plugin/marketplace.json`, `plugins/workflow/skills/plugin-audit/`.
