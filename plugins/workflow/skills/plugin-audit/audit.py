#!/usr/bin/env python3
"""List what installed Claude Code plugins run on this machine and flag the risky parts.

Read-only. Usage: audit.py [claude_dir]   (default: $CLAUDE_CONFIG_DIR or ~/.claude)
Self-check: audit.py --test
"""
import json
import os
import re
import sys
from pathlib import Path

NET = re.compile(r"\b(fetch\(|urlopen|requests\.(get|post)|https?\.request|XMLHttpRequest|WebSocket|"
                 r"curl |wget |nc |\.connect\()")
SECRETS = re.compile(r"(\.ssh/|\.aws/|\.netrc|keychain|security find-|_TOKEN|_SECRET|API_KEY)")
RUNNERS = {"npx", "uvx", "bunx", "pnpx", "pipx"}


def load(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return {}


def unpinned(cmd, args):
    """An npx/uvx-style command whose package is @latest or has no version: the next release runs unreviewed."""
    if os.path.basename(cmd or "") not in RUNNERS:
        return None
    pkgs = [a for a in args or [] if not a.startswith("-")]
    if not pkgs:
        return None
    pkg = pkgs[0]
    name, _, ver = pkg.rpartition("@") if pkg.count("@") > pkg.startswith("@") else (pkg, "", "")
    if not ver or ver in ("latest", "next") or not name:
        return f"`{cmd} {pkg}` is not pinned to a version"
    return None


def hook_commands(hooks):
    for entries in (hooks or {}).get("hooks", hooks or {}).values():
        for e in entries if isinstance(entries, list) else []:
            for h in e.get("hooks", []):
                if h.get("type") == "command":
                    yield h.get("command", "")


def scan_plugin(root):
    root = Path(root)
    manifest = load(root / ".claude-plugin" / "plugin.json")
    out = {"hooks": [], "mcp": [], "flags": []}
    hook_files = [root / "hooks" / "hooks.json"]
    hooks_field = manifest.get("hooks")
    for h in hooks_field if isinstance(hooks_field, list) else [hooks_field] if hooks_field else []:
        if isinstance(h, str):
            hook_files.append(root / h)
        elif isinstance(h, dict):
            out["hooks"] += list(hook_commands(h))
    for f in hook_files:
        out["hooks"] += list(hook_commands(load(f)))
    mcp = load(root / ".mcp.json")
    servers = mcp.get("mcpServers", mcp) | (manifest.get("mcpServers") if isinstance(manifest.get("mcpServers"), dict) else {})
    for sname, s in servers.items():
        if not isinstance(s, dict):
            continue
        where = s.get("url") or " ".join([s.get("command", "")] + s.get("args", []))
        out["mcp"].append(f"{sname}: {where}")
        if why := unpinned(s.get("command"), s.get("args")):
            out["flags"].append(f"MCP {sname}: {why}")
        if s.get("url", "").startswith("http://"):
            out["flags"].append(f"MCP {sname}: plain http, not https")
    # scripts the hooks run: scan files under hooks/ for network and secret access
    for f in sorted((root / "hooks").rglob("*")) if (root / "hooks").is_dir() else []:
        if f.is_file() and f.suffix in (".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".sh", "") and "test" not in f.name:
            try:
                text = f.read_text(errors="ignore")
            except OSError:
                continue
            rel = f.relative_to(root)
            if NET.search(text):
                out["flags"].append(f"hook file {rel}: talks to the network")
            if SECRETS.search(text):
                out["flags"].append(f"hook file {rel}: mentions credentials or secret stores")
    return out


def scan(claude_dir):
    plugins_dir = Path(claude_dir) / "plugins"
    installed = load(plugins_dir / "installed_plugins.json").get("plugins", {})
    markets = load(plugins_dir / "known_marketplaces.json")
    report = []
    for mname, m in sorted(markets.items()):
        src = m.get("source", {})
        trusted = (src.get("repo") or "").startswith("anthropics/")  # Anthropic reviews its own catalog
        if src.get("source") in ("github", "git", "url") and not (src.get("ref") or src.get("sha")) and not trusted:
            report.append(f"! marketplace {mname}: follows the default branch of {src.get('repo') or src.get('url')}")
        # third-party plugin entries inside a marketplace that aren't pinned to a commit
        for p in load(Path(m.get("installLocation", "")) / ".claude-plugin" / "marketplace.json").get("plugins", []):
            ps = p.get("source")
            if isinstance(ps, dict) and ps.get("source") in ("github", "url", "git-subdir") and not ps.get("sha"):
                report.append(f"! plugin {p.get('name')}@{mname}: git source without a pinned sha")
    for key, entries in sorted(installed.items()):
        for e in entries:
            res = scan_plugin(e["installPath"])
            report.append(f"\n{key} {e.get('version', '?')}")
            report += [f"  hook: {c}" for c in res["hooks"]]
            report += [f"  mcp:  {s}" for s in res["mcp"]]
            report += [f"  ! {f}" for f in res["flags"]]
    return report


def test():
    assert unpinned("npx", ["@playwright/mcp@latest"])
    assert unpinned("npx", ["-y", "@playwright/mcp"])
    assert unpinned("npx", ["some-pkg"])
    assert not unpinned("npx", ["-y", "@playwright/mcp@0.0.85"])
    assert not unpinned("npx", ["some-pkg@1.2.3"])
    assert not unpinned("node", ["x.js"])
    assert list(hook_commands({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "a"}]}]}})) == ["a"]
    print("plugin-audit: all checks pass")


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        test()
    else:
        d = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CLAUDE_CONFIG_DIR", os.path.expanduser("~/.claude"))
        print("\n".join(scan(d)))
