# Changelog

## Unreleased

### Added
- workflow 0.13.0: Codex proposes docs as file text from a read-only session; `codex.py docs` checks the paths (README.md, root .md, docs/; never ADRs, agent instruction files or plugin prompts) and shows the diff, `docs-apply` writes the checked text only if the manifest, paths and files are unchanged. No Codex call can write any more (ADR 0009)
- workflow 0.12.0: `codex.py` launcher, the only way Claude calls Codex read-only (ask, resume, review): fixed sandbox, no approvals, no MCP servers, ChatGPT connectors and plugins disabled, prompt on stdin, self-tested in `make check` (ADR 0008)

### Fixed
- workflow 0.11.1: `codex` skill runs from any directory (`--skip-git-repo-check`) and pins `approval_policy="never"` on every call, so Codex's auto-reviewer can no longer approve escalations out of the read-only sandbox
- `make setup` on Arch: set the stable Rust toolchain as default before adding rust-analyzer (the `rustup` package ships none), and link its rust-analyzer into `~/.local/bin`

### Changed
- engineering 0.2.1: ADR template is a short title and purpose, then `Technical details` (rich) and `Technologies and alternatives` (brief, skipped when empty); ADRs 0001-0005 rewritten in it
- engineering 0.1.1: `adr-manager` names ADRs `NNNN-short-title.adr` (Markdown inside); ADRs 0001-0004 renamed

### Added
- workflow 0.11.0, engineering 0.3.0: Codex runs every time at fixed points: review of every PR, critique of every ADR draft, root cause before every bug fix, second auditor in every security audit (ADR 0007)
- workflow 0.10.0: `codex` skill: Codex is a read-only second agent Claude calls through its CLI (ADR 0006)
- engineering 0.2.0, workflow 0.9.0: ADR first: no code for a feature until its ADR is approved; one decision per ADR, prerequisites numbered first, one ADR per PR (ADR 0005)
- `docs/adr/` with ADRs 0001-0004 recording the repo's existing decisions (all Accepted)
- workflow 0.8.0: `commit-style` starts every subject (except the initial commit) with an ADR number; minor changes reuse the latest ADR with a minor version, e.g. `[ADR-0010.3]`; `github-flow` tags the merge of a new major ADR (`ADR-0011`)
- engineering 0.1.0: `architecture-review`, `adr-manager` and `security-audit` skills; I approve every decision, audits run only when I ask
- workflow 0.7.0: `github-flow` keeps a `CLAUDE.md` in every repo and updates it in the PR that changes commands, layout or conventions; `new-project` creates one
- workflow 0.6.0: `new-project` skill: every new project gets a private GitHub repo under NobodyOne04 from the first commit
- workflow 0.5.0: session-start warning when a marketplace added from a local folder isn't on `main`
- workflow 0.4.0: `plugin-audit` skill: lists what installed plugins run and flags unpinned sources, network and credential use
- workflow 0.4.0: `github-flow` cleans up after a merge, bumps plugin versions in every PR of a plugin repo, runs each push on its own
- ponytail and diagram-design listed in this marketplace, pinned to a commit
- CI runs `make check` on every PR

### Changed
- dotfiles 0.1.4: repos renamed to `archminimal-hypr` (was `hyprland`) and `archminimal-setup` (was `linux_setup`, now in the map)
- dotfiles 0.1.3: the login screen repo is `archminimal-greeter` (was `sddm-login`), with its check
- dotfiles 0.1.2: map lists the `hyprland` and `sddm-login` repos (was a TODO) and how to check `hyprland`
- dotfiles 0.1.1: dotfiles changes go through `github-flow` (branch, PR, I merge) instead of commits to `main`; read each repo's `CLAUDE.md` first

## [0.1.0] - 2026-11-11

### Added
- workflow: `github-flow` skill: typed branches, a PR per change, a changelog line per PR, review-comment summaries
- workflow: hook that blocks PR merges and pushes to `main`, so only I merge
- workflow: `github-flow` opens each new PR in the browser for review

### Changed
- dev: pin the Playwright MCP version instead of running `@latest` from npm on every start
