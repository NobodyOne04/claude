#!/bin/sh
# Self-check for guard-main.py; run from anywhere. Exit 2 = blocked, 0 = allowed.
g="$(dirname "$0")/guard-main.py"
fail=0
t() { # expected-exit tool command [cwd]
  printf '{"tool_name":"%s","tool_input":{"command":"%s"},"cwd":"%s"}' "$2" "$3" "${4:-/tmp}" |
    python3 "$g" 2>/dev/null
  r=$?; [ "$r" = "$1" ] || { echo "FAIL ($r != $1): $2 $3"; fail=1; }
}
t 2 Bash "gh pr merge 3 --squash"
t 2 Bash "gh pr merge --auto 3"
t 2 Bash "gh api -X PUT repos/o/r/pulls/3/merge"
t 2 Bash "git push origin main"
t 2 Bash "git push origin +HEAD:refs/heads/main"
t 2 Bash "cd x && git push --force origin master"
t 2 Bash "git push --all"
t 0 Bash "git push -u origin feature/x"
t 0 Bash "git push origin main:feature/x"
t 0 Bash "git log main..HEAD"
t 2 Bash "git -c x=y --no-pager push origin main"
t 2 Bash "gh -R o/r pr merge 3"
t 2 Bash "gh api graphql -f query=mutation{mergePullRequest(input:{})}"
t 2 Bash "gh api -X PATCH repos/o/r/git/refs/heads/main"
t 2 Bash "bash -c 'git push origin main'"
t 0 Bash "git commit -m 'never git push to main'"
t 0 Bash "git -C . push origin feature/x"
t 2 Bash "git \\\\\\npush origin main"
t 2 Bash "/usr/bin/git push origin main"
t 2 Bash "cd /nonexistent && git push"
t 2 mcp__plugin_github_github__merge_pull_request ""
t 0 mcp__plugin_github_github__create_pull_request ""
[ "$fail" = 0 ] && echo "guard-main: all checks pass"
exit "$fail"
