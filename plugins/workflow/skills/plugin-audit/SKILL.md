---
name: plugin-audit
description: Security check of the Claude Code plugins, hooks, MCP servers and skills installed on this machine. Use after installing or updating a plugin or marketplace, when I ask "are my plugins safe", "audit my plugins/MCPs/skills", or before trusting a new third-party plugin.
---

# Plugin audit

Read-only: report first, change nothing until I say which fixes to make.

## 1. Inventory
Run `python3 -I "${CLAUDE_PLUGIN_ROOT}/skills/plugin-audit/audit.py"`. It lists, per installed
plugin, the hook commands and MCP servers it starts, and flags (`!`):
- marketplaces that follow someone's default branch (their next push installs unreviewed)
- `npx`/`uvx`-style MCP servers on `@latest` or without a version
- hook files that touch the network or mention credentials

A flag is a lead, not a verdict. Anthropic's own marketplace isn't flagged for following its branch.

## 2. Read what runs
For every hook command and every flagged file, open the code it actually runs and decide:
- **Data leaving the machine**: where does a network call go, what does it send, is it opt-in?
- **Credentials**: does it read tokens, `~/.ssh`, keychains, env secrets, and why?
- **Writes**: anything outside `~/.claude`, the plugin's own folder, or its documented config dir?
- **Exec**: does it run downloaded code, `eval`, or install packages at runtime?
- **Skills**: a `SKILL.md` that tells Claude to fetch and run remote scripts, disable checks,
  or send files somewhere counts the same as code doing it.

Skip tests, benchmarks and build scripts that only run when a maintainer runs them.

## 3. Report
One line per plugin: `ok`, or what's wrong and the concrete risk. Then the fixes, smallest
first. Usual fixes:
- third-party plugin: pin it in my `nobodyone` marketplace (`claude` repo) with a github source
  and `sha`, instead of adding its own marketplace
- MCP server: pin the package version in `.mcp.json`
- anything that sends data out unasked: uninstall, and say so plainly

Changes to my `claude` repo go through `github-flow`.
