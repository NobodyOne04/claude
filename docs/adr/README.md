# Architecture Decision Records

Format and lifecycle: `docs/adr/NNNN-short-title.adr`, statuses Proposed, Accepted, Rejected, Deprecated, Superseded.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-repo-is-a-plugin-marketplace.adr) | The setup repo is a Claude Code plugin marketplace | Accepted |
| [0002](0002-pin-third-party-plugins-by-sha.adr) | Pin third-party plugins by commit, audit before bumping | Accepted |
| [0003](0003-only-the-owner-merges-to-main.adr) | Only the owner merges to main, enforced by a hook | Accepted |
| [0004](0004-stdlib-python-scripts-with-self-tests.adr) | Plugin scripts are stdlib Python with a built-in self-test | Accepted |
| [0005](0005-adr-before-code-one-adr-per-pr.adr) | ADR before code, granular ADRs, one ADR per PR | Accepted |
| [0006](0006-codex-read-only-second-agent.adr) | Codex is a read-only second agent, called through its CLI | Accepted |
| [0007](0007-where-codex-runs-in-the-flow.adr) | Where Codex runs in the flow | Accepted |
| [0008](0008-codex-calls-go-through-one-launcher.adr) | Codex calls go through one tested launcher | Accepted |
