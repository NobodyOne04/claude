# Changelog

## Unreleased

### Added
- workflow 0.5.0: session-start warning when a marketplace added from a local folder isn't on `main`
- workflow 0.4.0: `plugin-audit` skill: lists what installed plugins run and flags unpinned sources, network and credential use
- workflow 0.4.0: `github-flow` cleans up after a merge, bumps plugin versions in every PR of a plugin repo, runs each push on its own
- ponytail and diagram-design listed in this marketplace, pinned to a commit
- CI runs `make check` on every PR

## [0.1.0] - 2026-11-11

### Added
- workflow: `github-flow` skill: typed branches, a PR per change, a changelog line per PR, review-comment summaries
- workflow: hook that blocks PR merges and pushes to `main`, so only I merge
- workflow: `github-flow` opens each new PR in the browser for review

### Changed
- dev: pin the Playwright MCP version instead of running `@latest` from npm on every start
