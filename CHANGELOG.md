# Changelog

## Unreleased

## [0.1.0] - 2026-11-11

### Added
- workflow: `github-flow` skill: typed branches, a PR per change, a changelog line per PR, review-comment summaries
- workflow: hook that blocks PR merges and pushes to `main`, so only I merge
- workflow: `github-flow` opens each new PR in the browser for review

### Changed
- dev: pin the Playwright MCP version instead of running `@latest` from npm on every start
