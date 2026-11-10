#!/usr/bin/env python3
"""PreToolUse hook: only the user merges into main. Blocks PR merges and pushes to main/master."""
import json
import re
import subprocess
import sys

PROTECTED = {"main", "master"}


def block(why):
    print(f"Blocked by the workflow plugin: {why}. Work on a feature branch and open a PR; "
          "only the user merges into main.", file=sys.stderr)
    sys.exit(2)


def current_branch(cwd):
    r = subprocess.run(["git", "-C", cwd or ".", "branch", "--show-current"],
                       capture_output=True, text=True)
    return r.stdout.strip()


def check_push(args, cwd):
    if any(a in ("--all", "--mirror") for a in args):
        block("pushing every branch")
    positional = [a for a in args if not a.startswith("-")]
    refspecs = positional[1:]  # first positional is the remote
    # no refspec, or HEAD: pushes the current branch (to its same-named upstream)
    targets = [r.lstrip("+").split(":")[-1] for r in refspecs] or ["HEAD"]
    for t in targets:
        t = t.removeprefix("refs/heads/")
        if t == "HEAD":
            t = current_branch(cwd)
        if t in PROTECTED:
            block(f"pushing to {t}")


def main():
    d = json.load(sys.stdin)
    tool = d.get("tool_name", "")
    if tool.endswith("merge_pull_request"):
        block("merging a pull request")
    if tool != "Bash":
        return
    cmd = d.get("tool_input", {}).get("command", "")
    cwd = d.get("cwd")
    if re.search(r"\bgh\s+pr\s+merge\b", cmd) or re.search(r"/pulls/\d+/merge\b", cmd):
        block("merging a pull request")
    for seg in re.split(r"&&|\|\||;|\||\n", cmd):
        m = re.search(r"\bgit\s+(?:-C\s+(\S+)\s+)?push\b(.*)", seg)
        if m:
            check_push(m.group(2).split(), m.group(1) or cwd)


main()
