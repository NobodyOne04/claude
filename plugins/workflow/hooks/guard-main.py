#!/usr/bin/env python3
"""PreToolUse hook: only the user merges into main. Blocks PR merges and pushes to main/master."""
import json
import os
import re
import shlex
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
            if not t:
                block("pushing from a folder whose branch I can't tell")
        if t in PROTECTED:
            block(f"pushing to {t}")


MERGE_PATTERNS = [
    r"\bgh\b[^\n;&|]*\bpr\s+merge\b",           # gh pr merge, also with flags in between
    r"/pulls/\d+/merge\b",                         # REST merge (gh api, curl)
    r"\b(mergePullRequest|enablePullRequestAutoMerge)\b",  # GraphQL
    r"/git/refs/heads/(main|master)\b",             # moving the ref directly
]
GIT_OPTS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
SHELLS = {"sh", "bash", "zsh", "eval", "xargs"}


def segments(cmd):
    """Yield each simple command as a token list; a line shlex can't parse only matters if it pushes."""
    for line in cmd.replace("\\\n", " ").splitlines():  # join `\` continuations
        lex = shlex.shlex(line, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        try:
            toks = list(lex)
        except ValueError:
            if re.search(r"\bgit\b.*\bpush\b", line):
                block("a git push I can't parse; run it on its own line")
            continue
        seg = []
        for t in toks:
            if t and set(t) <= set(";&|()"):
                yield seg
                seg = []
            else:
                seg.append(t)
        yield seg


def main():
    d = json.load(sys.stdin)
    tool = d.get("tool_name", "")
    if tool.endswith("merge_pull_request"):
        block("merging a pull request")
    if tool != "Bash":
        return
    cmd = d.get("tool_input", {}).get("command", "")
    cwd = d.get("cwd")
    if any(re.search(p, cmd) for p in MERGE_PATTERNS):
        block("merging a pull request or moving main")
    for seg in segments(cmd):
        if seg[:1] == ["cd"] and len(seg) > 1:
            cwd = os.path.join(cwd or ".", os.path.expanduser(seg[1]))
            continue
        if SHELLS & set(seg) and any(re.search(r"\bgit\b.*\bpush\b", t) for t in seg):
            block("a git push inside a nested shell; run it directly")
        names = [os.path.basename(t) for t in seg]  # /usr/bin/git counts as git
        if "git" not in names:
            continue
        i, gcwd = names.index("git") + 1, cwd
        while i < len(seg) and seg[i].startswith("-"):
            if seg[i] in GIT_OPTS_WITH_ARG and i + 1 < len(seg):
                if seg[i] == "-C":
                    gcwd = os.path.join(gcwd or ".", os.path.expanduser(seg[i + 1]))
                i += 2
            else:
                i += 1
        if i < len(seg) and seg[i] == "push":
            check_push(seg[i + 1:], gcwd)


main()
