# claude

My Claude Code setup: skills, plugins and MCP servers, shared between the Mac and Arch.
The repo is a plugin marketplace, so every machine installs from it the same way.

## Install

```
/plugin marketplace add NobodyOne04/claude
/plugin install workflow@nobodyone
/plugin install dotfiles@nobodyone
```

Update later with `/plugin marketplace update nobodyone`.

## Layout

```
.claude-plugin/marketplace.json   # lists the plugins below
plugins/
  workflow/                       # how I work, in every repo
    .claude-plugin/plugin.json
    skills/commit-style/SKILL.md
```

A plugin can hold `skills/`, `agents/`, `commands/`, `hooks/hooks.json` and `.mcp.json` (MCP servers).

## Plugins

| Plugin | What's in it |
|---|---|
| `workflow` | `commit-style`: commit messages and git habits |
| `dotfiles` | `dotfiles`: map, house style and checks for my zsh, nvim, tmux, Ghostty and Arch configs |

## Develop

`make check` validates the marketplace and every plugin.
