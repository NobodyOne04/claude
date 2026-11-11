# Changelog

## Unreleased

### Added
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
