---
name: dotfiles
description: Map, conventions and checks for my dotfiles repos (zsh, nvim, tmux, Ghostty, Arch desktop "archminimal"). Use whenever a task touches shell aliases or functions, prompt, git/direnv/atuin/lazygit config, Neovim config or plugins, tmux, Ghostty, keybindings, the archminimal theme, or "my config", "my setup", "my dotfiles", on macOS or Arch.
---

# Dotfiles

I run the same configs on a Mac and an Arch Linux desktop (Hyprland, "archminimal").
Every config is its own git repo under `~/projects/`, symlinked into place.
Edit the repo, never the symlink target's copy, and never a `.bak-*` file.

## Map

| Repo (`~/projects/…`) | GitHub | Linked to | What |
|---|---|---|---|
| `zsh` | `NobodyOne04/zsh` | `~/.zshrc`, `~/.config/{git,direnv,atuin,lazygit}/…` | shell, prompt (p10k), aliases, helpers, git config + global hooks, direnv, atuin, lazygit |
| `nvim` | `NobodyOne04/nvim` | `~/.config/nvim` | Neovim (lazy.nvim) |
| `tmux` | `NobodyOne04/tmux` | `~/.config/tmux`, `~/.local/bin/tms` | tmux, `tms` session picker |
| `~/.config/ghostty` (not linked, the repo itself) | `NobodyOne04/ghostty` | — | Ghostty terminal |
| Arch desktop | _TODO: repo name_ | _TODO_ | Hyprland, bar, launcher, login screen |
| `claude` | `NobodyOne04/claude` | Claude plugin marketplace | skills, plugins, MCP (this skill lives here) |

Check what is linked: `make status` in `zsh` and `tmux`; `readlink ~/.config/nvim`.

Before working in a repo, read its `CLAUDE.md` if it has one (`zsh`, `nvim`, `claude`): where changes go,
how to test, and gotchas that already cost time. Keep it current when you learn a new one.

### Where things go

**zsh**: `zshrc` only sources `conf.d/*.zsh` in order:
- `00-env` env and PATH · `10-options` · `20-plugins` · `30-completion` · `40-tools`
- `50-aliases` general aliases · `60-functions` helpers · `70-devops` docker/k8s/terraform/helm/aws
- `90-local` sources the untracked per-machine files (below)
- `lib/*.zsh` bigger helper groups (e.g. `lib/git.zsh`), `p10k.zsh` the prompt
- `git/` git config, global ignore, global hooks (gitleaks on every commit)

**nvim**: `lua/config/{options,keymaps,autocmds,lazy}.lua`; plugins by theme in
`lua/plugins/{core,editor,coding,lsp,treesitter,ui,tools,notebook,tmux}.lua`.
`lazy-lock.json` pins plugins: commit it when plugins change.

**tmux**: `tmux.conf` sources `conf/{options,keys,plugins,theme}.conf`; scripts in `bin/`.

## House style

- **Guard on the tool.** Define an alias only if its command exists:
  `(( $+commands[bat] )) && alias b='bat'`.
- **One config, both OSes.** Branch inside the file, never fork it:
  `[[ $OSTYPE == darwin* ]]`, then Wayland (`$WAYLAND_DISPLAY`), then X11.
  Same idea in Lua (`vim.fn.has("mac")`) and tmux (`if-shell 'uname | grep -q Darwin'`).
- **Comment the why**, briefly, on the same line or just above. Match the existing tone.
- **Helpers:** use `function name { … }` (alias-proof); check `alias` / `whence -a` for
  collisions with oh-my-zsh before naming one (`gclean` broke this way once).
- **Keys:** Alt-h/j/k/l moves between nvim splits and tmux panes (smart-splits); in nvim,
  `s` is mini.jump2d. Check for clashes across nvim, tmux and Ghostty before binding a key.
- **Look ("archminimal"):** one cyan accent `#00e5ff`, background `#18191d`, transparent
  backgrounds, rounded borders, quiet UI. Full palette is in the Ghostty `config`.
  The OS logo (Arch / Apple) shows in the prompt, nvim statusline and start screen.
- **Startup stays fast and silent.** Nothing that runs a network call or prints at shell start.

## Secrets

Never put secrets in these repos. Per-machine files, untracked:
- `~/.config/zsh/local.zsh` machine-only settings
- `~/.config/zsh/secrets.zsh` API keys (chmod 600; add with `secret-add NAME`)
- per-project: `.env.sops` encrypted with sops + age (`env-encrypt`, `env-edit`)

## Check before you commit

Run the repo's check and show me the result:

| Repo | Command | What it does |
|---|---|---|
| `zsh` | `make check` | `make lint` (`zsh -n` on every file, git/direnv/hooks parse; CI runs it) + interactive startup prints nothing |
| `nvim` | `make check` | headless start, then every plugin loaded and a file per language opened; fails on errors |
| `tmux` | `make check` | loads the config in a throwaway server |
| `ghostty` | `ghostty +validate-config` | config parses |
| `claude` | `make check` | `claude plugin validate`, hook and script self-tests (CI runs it) |

To try a zsh change in a fresh shell: `zsh -ic '<command>'`, or tell me to run `reload`.

## Docs

Each repo's README has tables of keys, aliases and helpers. When you add or change one,
update the README in the same commit.

## Commit and sync

- Every change goes through the `github-flow` skill, like any other repo: branch, `CHANGELOG.md` line,
  PR opened in the browser, I merge (squash only). Commits follow `commit-style`. One repo per PR.
- These repos are the live config (`~/.zshrc`, `~/.config/nvim` point at the checkout): after pushing a
  branch, switch back to `main` unless I'm trying the change; after I merge, `git switch main && git pull`.
- After a merge, remind me to `git pull` on the other machine (and `make sync` for nvim if
  `lazy-lock.json` changed, `make link` if a new linked file was added), and `reload` / restart nvim here.

## Don't

- Don't run `make install`, `make link`/`unlink`, `chsh` or package installs without asking.
- `p10k.zsh` is customised by hand (OS logo segment, archminimal colours): edit it in place,
  never regenerate it with `p10k configure`.
- Don't touch `~/.oh-my-zsh`, `~/.local/share/nvim/lazy` or other installed plugin code.
