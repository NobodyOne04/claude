# claude

My Claude Code plugin marketplace (`nobodyone`): skills, hooks and MCP servers for every machine.
Setup and plugin list: `README.md`.

## Commands
- `make check`: validate the marketplace and every plugin, self-test the hooks and the audit
  script. CI runs it on every PR; run it before pushing.
- `make setup`: install everything on a fresh machine.

## Layout
- `.claude-plugin/marketplace.json`: the plugin list. Third-party plugins are pinned by `sha`.
- `plugins/<name>/.claude-plugin/plugin.json`: each plugin's manifest and `version`.
- `plugins/workflow/skills/*/SKILL.md`: my working rules (commits, GitHub flow, new projects, audit,
  `codex`: the read-only second agent).
- `plugins/engineering/skills/*/SKILL.md`: architecture review, ADRs, security audits.
- `docs/adr/`: decision records for this repo (`adr-manager`).
- `plugins/workflow/hooks/`: `guard-main.py` blocks merges and pushes to `main`
  (tests: `test-guard.sh`); `marketplace-branch.py` warns when this repo isn't on `main`.

## Conventions
- Every PR bumps `version` in the `plugin.json` of each plugin it touches and adds a
  `CHANGELOG.md` line naming it (`github-flow`).
- A major change starts with an ADR I approve before any code; one decision per ADR, one ADR
  per PR, prerequisites numbered first (ADR 0005).
- Python scripts carry their own `--test` self-check; run with `python3 -I`, stdlib only.
- Bump a third-party `sha` only after running `plugin-audit` on the new commit.
- Leave this repo on `main` when done: the local marketplace installs whatever is checked out.

## Gotchas
- Run `git push` as a command of its own: the merge guard refuses pushes chained with `&&`.
- Auto mode refuses some actions even when asked: edits to `~/.claude/settings.json` that widen
  trust or permissions, and deleting remote branches. Give me the exact command to run with `! …`.
- Never rewrite `~/.claude/settings.json` whole: merge into it (an overwrite once dropped every
  enabled plugin and the marketplace entry).
- After a merge: `/plugin marketplace update nobodyone`, then `/reload-plugins`. An installed plugin
  only changes when its `version` does.
- zsh expands a leading `=`: `echo ===` fails with "== not found". Quote it.
- The dotfiles repos (`zsh`, `nvim`, `tmux`, `ghostty`) are described in the `dotfiles` skill; when
  a repo's check command or flow changes, update its row there.
