---
name: github-flow
description: Branches, pull requests, changelog and review rules for my GitHub repos. Use whenever you start a change in a repo with a GitHub remote, before creating a branch, committing, pushing, opening or updating a PR, answering PR review comments, or cutting a release/version.
---

# GitHub flow

Applies to every repo with a GitHub remote. Commit messages still follow `commit-style`.

## Never touch `main` yourself
- Never commit to `main`, never push to `main`, never merge into it.
- Never merge a PR: no `gh pr merge` (not even `--auto`), no `merge_pull_request` MCP call,
  no merge button through a browser. **Only I merge.** A hook in this plugin blocks these;
  if it fires, don't look for a way around it.
- When the PR is ready, stop and give me the link.

## One branch per change
Start from an up-to-date `main` (`git switch main && git pull --ff-only`), then
`git switch -c <type>/<short-slug>`. Lowercase, hyphens, 2-5 words.

| Type | For |
|---|---|
| `feature/` | new functionality |
| `bug/` | fixing something broken |
| `hotfix/` | urgent fix for something broken right now |
| `minor/` | small tweak: wording, a value, a one-line change |
| `refactor/` | restructuring, no behaviour change |
| `docs/` | documentation only |
| `chore/` | deps, config, CI, tooling |

If the work comes from a GitHub issue, put its number first in the slug and close it from the
PR body: `bug/42-login-crash` + `Closes #42`.

One branch is one topic. Something unrelated comes up: new branch, new PR.

## Changelog: every PR adds a line
- The repo keeps `CHANGELOG.md` at its root ([Keep a Changelog](https://keepachangelog.com)
  format). Create it if missing:
  ```
  # Changelog

  ## Unreleased
  ```
- Every PR adds one line under `## Unreleased`, in the matching section
  (`### Added` for feature, `### Fixed` for bug/hotfix, `### Changed` for
  minor/refactor/docs/chore, `### Removed` when something goes away):
  `- github-flow skill: branch, PR and changelog rules`.
  Plain words, same voice as the commit subject, no 🤖.
- **Releasing a version** (only when I ask): rename `## Unreleased` to
  `## [x.y.z] - YYYY-MM-DD`, add a fresh empty `## Unreleased` above it, bump the version
  where the repo keeps one (`plugin.json`, `package.json`, `Cargo.toml`, ...). Semver: anything
  under Added → minor bump, otherwise patch; breaking changes → ask me. This goes through its
  own `chore/release-x.y.z` PR. After I merge it, tag `vx.y.z` on `main` only if I ask.

## Commits on the branch: squash when needed
- Before opening the PR, look at `git log main..HEAD`. If there are fixups, WIP or
  "oops" commits, squash them into one (or a few that each make sense alone):
  `git reset --soft $(git merge-base main HEAD)` then commit again with a proper message.
  Interactive rebase isn't available.
- After the branch is pushed, rewriting it needs `git push --force-with-lease`, and only on
  your own branch, never on `main`.
- I merge with **Squash and merge**, so the PR title becomes the commit on `main`: write it
  like a commit subject (`commit-style`, ending in ` 🤖`).

## Opening the PR
- Push with `git push -u origin <branch>`, then `gh pr create --base main`.
- Use the repo's PR template if it has one (`.github/pull_request_template.md` or
  `.github/PULL_REQUEST_TEMPLATE/`). Otherwise the body is:
  ```
  ## Why
  <what was wrong or missing>

  ## What changed
  - <bullet per change>

  ## Testing
  <how you checked it, or "not tested" and why>

  ## Changelog
  <the line you added>
  ```
- Right after creating it, open it in my browser: `gh pr view <n> --web`.
- Check that CI passes (`gh pr checks <n>`) before telling me it's ready.

## Review comments: answer each, then summarize
When I (or anyone) leave comments on the PR and ask you to address them:
1. Read all of them: `gh pr view <n> --comments` plus inline ones,
   `gh api repos/{owner}/{repo}/pulls/<n>/comments`.
2. Fix on the same branch, new commits (squash before I merge only if I ask).
3. Reply to each inline comment with what you did, or why you didn't.
4. Post **one summary comment** on the PR: one line per comment, `fixed in <sha>`,
   `won't fix: <why>` or `question for you: <...>`. Update the PR body if the change grew.
5. Give me the link again. Don't resolve threads opened by others; I resolve them.
