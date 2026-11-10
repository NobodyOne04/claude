# claude

My Claude Code setup: skills, plugins and MCP servers, shared between the Mac and Arch.
The repo is a plugin marketplace, so every machine installs from it the same way.

## Install

On a new machine, clone the repo and run `make setup`. It adds this repo as a marketplace,
installs every plugin (plus `rust-analyzer-lsp`, `claude-code-setup`, `security-guidance`, `github`
(needs `GITHUB_PERSONAL_ACCESS_TOKEN` set), `feature-dev` and
[superpowers](https://github.com/obra/superpowers) from the official marketplace, and
[ponytail](https://github.com/DietrichGebert/ponytail) and
[diagram-design](https://github.com/cathrynlavery/diagram-design), which this marketplace lists pinned to a
commit so their updates only arrive when I bump the `sha` in `marketplace.json`),
installs the language servers (brew on macOS, pacman on Arch), installs Chromium for Playwright,
then runs `make doctor`. Running it again only installs what's missing.

| Target | Does |
|---|---|
| `make setup` | all of the below |
| `make plugins` | marketplace + plugins |
| `make lsp` | language servers missing from `PATH` |
| `make browser` | Chromium for the Playwright MCP |
| `make doctor` | which language servers are missing, MCP connection status |
| `make check` | validate the marketplace and every plugin, self-test the hook and the audit script (CI runs it on every PR) |

Or by hand from inside Claude:

```
/plugin marketplace add NobodyOne04/claude
/plugin install workflow@nobodyone
/plugin install dotfiles@nobodyone
/plugin install dev@nobodyone
```

Update later with `/plugin marketplace update nobodyone`.

## Layout

```
.claude-plugin/marketplace.json   # lists the plugins below
plugins/
  workflow/                       # how I work, in every repo
    .claude-plugin/plugin.json
    skills/commit-style/SKILL.md
    skills/github-flow/SKILL.md
    skills/plugin-audit/          # SKILL.md + audit.py
    skills/new-project/SKILL.md
    hooks/hooks.json              # guard-main.py: no merges/pushes to main
                                  # marketplace-branch.py: warn if this repo isn't on main
```

A plugin can hold `skills/`, `agents/`, `commands/`, `hooks/hooks.json` and `.mcp.json` (MCP servers).

## Plugins

| Plugin | What's in it |
|---|---|
| `workflow` | `commit-style`: commit messages. `github-flow`: typed branches (`feature/`, `bug/`, ...), PR per change, `CHANGELOG.md` line per PR, `CLAUDE.md` kept current, review-comment summaries, cleanup after merge. `plugin-audit`: security check of installed plugins, hooks and MCP servers. `new-project`: every new project starts as a private GitHub repo, so it's backed up from the first commit. Hooks: block PR merges and pushes to `main` (only I merge); warn at session start when a local-folder marketplace isn't on `main` |
| `ponytail`, `diagram-design` | third-party, pinned to a reviewed commit; run `plugin-audit` before bumping the `sha` |
| `dev` | MCP: Context7 (current library docs), Playwright (browser). LSP: Go, Python, Lua, TS/JS, Bash, YAML |
| `dotfiles` | `dotfiles`: map, house style and checks for my zsh, nvim, tmux, Ghostty and Arch configs |

## Develop

`make check` validates the marketplace and every plugin, and self-tests the merge guard.

Changes go through a branch and a PR (see `github-flow`); every PR adds a line to `CHANGELOG.md`.

## `dev` plugin setup (once per machine)

**Context7** needs a login: in Claude run `/mcp`, pick `plugin:dev:context7`, authenticate in the browser.

**Playwright** runs through `npx` (needs Node). If it reports a missing browser:
`make browser`. Its version is pinned in `plugins/dev/.mcp.json`; bump it on purpose, not via `@latest`.

**Language servers** must be on `PATH`; a missing one only disables that language.

| Language | Server | Arch | macOS |
|---|---|---|---|
| Go | `gopls` | `pacman -S gopls` | `go install golang.org/x/tools/gopls@latest` |
| Python | `pyright-langserver` | `pacman -S pyright` | `brew install pyright` |
| Lua | `lua-language-server` | `pacman -S lua-language-server` | `brew install lua-language-server` |
| TS/JS | `typescript-language-server` | `pacman -S typescript-language-server` | `brew install typescript-language-server` |
| Bash | `bash-language-server` | `pacman -S bash-language-server` | `brew install bash-language-server` |
| YAML | `yaml-language-server` | `pacman -S yaml-language-server` | `brew install yaml-language-server` |

nvim's mason installs these too, in `~/.local/share/nvim/mason/bin`, which is not on `PATH` by default.

Check: `claude --plugin-dir plugins/dev mcp list` and `claude --plugin-dir plugins/dev plugin details dev`.
