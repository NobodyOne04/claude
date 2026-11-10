#!/usr/bin/env python3
"""SessionStart hook: warn when a marketplace added from a local folder isn't on main.

Such a marketplace installs whatever is checked out, so a feature branch left there
quietly becomes what every new session loads. Never blocks; prints nothing when all is fine.
Self-check: marketplace-branch.py --test
"""
import json
import os
import subprocess
import sys
from pathlib import Path


def branch(path):
    r = subprocess.run(["git", "-C", path, "branch", "--show-current"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None  # None: not a git repo


def warnings(markets):
    out = []
    for name, m in sorted(markets.items()):
        src = m.get("source", {})
        if src.get("source") != "directory":
            continue
        b = branch(src.get("path", ""))
        if b is not None and b not in ("main", "master"):
            out.append(f"marketplace {name} ({src['path']}) is on branch '{b or 'detached HEAD'}', "
                       f"so plugins install from it, not from main. Switch it back: git -C {src['path']} switch main")
    return out


def main():
    claude_dir = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    try:
        markets = json.loads((claude_dir / "plugins" / "known_marketplaces.json").read_text())
    except (OSError, ValueError):
        return
    w = warnings(markets)
    if w:
        msg = "workflow: " + "\n".join(w)
        print(json.dumps({"systemMessage": msg,
                          "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg}}))


def test():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        git = lambda *a: subprocess.run(["git", "-C", d, *a], capture_output=True, check=True)
        git("init", "-q", "-b", "main")
        m = {"local": {"source": {"source": "directory", "path": d}},
             "remote": {"source": {"source": "github", "repo": "o/r"}}}
        assert warnings(m) == [], warnings(m)
        git("switch", "-q", "-c", "feature/x")
        w = warnings(m)
        assert len(w) == 1 and "feature/x" in w[0], w
    assert warnings({"gone": {"source": {"source": "directory", "path": "/nonexistent"}}}) == []
    print("marketplace-branch: all checks pass")


if __name__ == "__main__":
    test() if sys.argv[1:] == ["--test"] else main()
