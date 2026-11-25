#!/usr/bin/env python3
"""Claude's only way to call Codex: every call read-only, no approvals, no MCP (ADR 0008).

  codex.py ask [--repo DIR]            prompt on stdin; new thread
  codex.py resume THREAD_ID [--repo DIR]  prompt on stdin; continue a thread
  codex.py review [--base REF]         from the repo root; review the branch against REF
  codex.py --test                      self-check with a fake codex

Success prints `thread: <id>` (or the review header), then Codex's final message.
Any failure prints only `Codex: skipped (<reason>)` and exits 3.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

# Not overridable: the read-only guarantee lives here, not in the caller's command line.
FIXED = ["-c", 'sandbox_mode="read-only"', "-c", 'approval_policy="never"',
         "-c", "mcp_servers={}"]
# Built-in features whose tools act outside the sandbox: `apps` alone exposes ChatGPT
# connectors that deploy sites, change sharing and settings (seen on 0.172.0, 2026-11-25).
for _f in ("apps", "plugins", "remote_plugin", "browser_use", "browser_use_external",
           "computer_use", "image_generation", "skill_mcp_dependency_install", "tool_suggest"):
    FIXED += ["--disable", _f]
UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
SKIPPED = 3


class Skip(Exception):
    pass


def skip_line(text):
    """The whole `Codex: skipped (...)` line, at most 200 chars, home shortened to ~."""
    text = " ".join(str(text).split()).replace(os.path.expanduser("~"), "~") or "no reason given"
    return f"Codex: skipped ({text[:200 - len('Codex: skipped ()')]})"


def last_line(stderr):
    # codex echoes the whole session (prompt included) on stderr; the error is the last line
    lines = [x for x in stderr.decode("utf-8", "replace").splitlines() if x.strip()]
    return lines[-1] if lines else "no error output"


def run(cmd, stdin=b"", cwd=None):
    try:
        return subprocess.run(cmd, input=stdin, capture_output=True, cwd=cwd)
    except OSError as e:
        raise Skip(f"{cmd[0]}: {e.strerror}")


def preflight():
    if not shutil.which("codex"):
        raise Skip("codex not installed")
    if run(["codex", "login", "status"]).returncode != 0:
        raise Skip("codex not logged in")


def last_message(stdout):
    """Thread id and final agent message from `codex exec --json` events."""
    thread, message = None, None
    for line in stdout.decode("utf-8", "replace").splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if not isinstance(ev, dict):
            continue
        thread = thread or ev.get("thread_id")
        item = ev.get("item") or {}
        if ev.get("type") == "item.completed" and item.get("type") == "agent_message":
            message = item.get("text")
    return thread, message


def codex_exec(args, prompt, repo):
    if repo and not os.path.isdir(repo):
        raise Skip(f"--repo {repo}: not a directory")
    # outside a repo Codex refuses to start without this; it grants nothing
    cmd = ["codex", "exec", *args, "--json", *FIXED, "--skip-git-repo-check", "-"]
    p = run(cmd, prompt, cwd=repo)
    if p.returncode != 0:
        raise Skip(f"codex exited {p.returncode}: {last_line(p.stderr)}")
    thread, message = last_message(p.stdout)
    if not message:
        raise Skip("no final message from codex")
    return thread, message


def ask(a, prompt):
    thread, message = codex_exec([], prompt, a.repo)
    if not UUID.match(str(thread)):
        raise Skip("no valid thread id from codex")
    return f"thread: {thread}\n{message}"


def resume(a, prompt):
    if not UUID.match(a.thread_id):
        raise Skip("thread id is not a UUID")
    thread, message = codex_exec(["resume", a.thread_id], prompt, a.repo)
    return f"thread: {thread or a.thread_id}\n{message}"


def git(*args):
    p = run(["git", *args])
    if p.returncode != 0:
        # fixed text: git's stderr can carry a remote URL with credentials, and this goes in PRs
        raise Skip(f"git {args[0]} failed")
    return p.stdout.decode().strip()


def review(a, _prompt):
    if a.base.startswith("-"):
        raise Skip("base must be a ref")
    # codex reviews `git diff <base>`, which includes uncommitted edits: the header would lie
    if git("status", "--porcelain", "--untracked-files=no"):
        raise Skip("uncommitted changes; commit them before the review")
    remote, _, branch = a.base.partition("/")
    if branch and remote in git("remote").split():
        git("fetch", "--quiet", remote, branch)
        ref = "FETCH_HEAD"  # the tracking ref may not update under a narrow refspec
    else:
        ref = a.base
    base, head = git("rev-parse", "--verify", ref + "^{commit}"), git("rev-parse", "HEAD")
    p = run(["codex", "review", "--base", base, *FIXED])
    if p.returncode != 0:
        raise Skip(f"codex review exited {p.returncode}: {last_line(p.stderr)}")
    text = p.stdout.decode("utf-8", "replace").strip()
    if not text:
        raise Skip("codex review printed nothing")
    if git("rev-parse", "HEAD") != head:
        raise Skip("HEAD moved during the review; run it again")
    return f"Codex review of {base[:12]}..{head[:12]}\n{text}"


def main(argv):
    ap = argparse.ArgumentParser(prog="codex.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ask")
    p.add_argument("--repo")
    p.set_defaults(fn=ask, reads_prompt=True)
    p = sub.add_parser("resume")
    p.add_argument("thread_id")
    p.add_argument("--repo")
    p.set_defaults(fn=resume, reads_prompt=True)
    p = sub.add_parser("review")
    p.add_argument("--base", default="origin/main")
    p.set_defaults(fn=review, reads_prompt=False)
    a = ap.parse_args(argv)
    try:
        prompt = sys.stdin.buffer.read() if a.reads_prompt else b""
        if a.reads_prompt and not prompt.strip():
            raise Skip("empty prompt on stdin")
        preflight()
        print(a.fn(a, prompt))
        return 0
    except Skip as e:
        print(skip_line(e))
        return SKIPPED


def self_test():
    import contextlib
    import io
    import tempfile

    tmp = tempfile.mkdtemp()
    log, out = os.path.join(tmp, "log.json"), os.path.join(tmp, "out")
    fake = os.path.join(tmp, "bin", "codex")
    os.makedirs(os.path.dirname(fake))
    with open(fake, "w") as f:
        f.write(f"""#!{sys.executable} -I
import json, os, sys
if sys.argv[1:3] == ["login", "status"]:
    sys.exit(int(os.environ.get("FAKE_LOGIN_RC", "0")))
json.dump({{"argv": sys.argv[1:], "stdin": sys.stdin.read(), "cwd": os.getcwd()}},
          open({log!r}, "w"))
sys.stderr.write(os.environ.get("FAKE_ERR", ""))
sys.stdout.write(open({out!r}).read())
sys.exit(int(os.environ.get("FAKE_RC", "0")))
""")
    os.chmod(fake, 0o755)
    env = dict(os.environ, PATH=os.path.dirname(fake) + os.pathsep + os.environ["PATH"])
    tid = "01a2123e-43a2-7402-a22b-fa8f72410a03"
    events = "\n".join(json.dumps(e) for e in [
        {"type": "thread.started", "thread_id": tid},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "first"}},
        {"type": "item.completed", "item": {"type": "command_execution"}},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "final"}},
    ]) + "\nnot json\n"

    def call(argv, stdin="", stdout=events, **extra):
        with open(out, "w") as f:
            f.write(stdout)
        if os.path.exists(log):
            os.remove(log)
        saved = dict(os.environ)
        os.environ.clear()
        os.environ.update(env, **extra)
        buf = io.StringIO()
        sys.stdin = io.TextIOWrapper(io.BytesIO(stdin.encode()))
        try:
            with contextlib.redirect_stdout(buf):
                rc = main(argv)
        finally:
            sys.stdin = sys.__stdin__
            os.environ.clear()
            os.environ.update(saved)
        seen = json.load(open(log)) if os.path.exists(log) else None
        return rc, buf.getvalue(), seen

    # spelled out here, not taken from FIXED, so dropping a flag there fails the test
    want = ["-c", 'sandbox_mode="read-only"', "-c", 'approval_policy="never"',
            "-c", "mcp_servers={}"]
    for f in ("apps", "plugins", "remote_plugin", "browser_use", "browser_use_external",
              "computer_use", "image_generation", "skill_mcp_dependency_install", "tool_suggest"):
        want += ["--disable", f]

    def has_fixed(argv):
        # all the flags, in order, and no other -c that could override one
        return any(argv[i:i + len(want)] == want for i in range(len(argv))) and \
            argv.count("-c") == 3 and "--enable" not in argv

    nasty = "it's `rm -rf` \"$HOME\" $(x)\nline2\n"
    rc, text, seen = call(["ask"], nasty)
    assert rc == 0 and text == f"thread: {tid}\nfinal\n", text
    assert seen["argv"][:2] == ["exec", "--json"] and has_fixed(seen["argv"]), seen
    assert "--skip-git-repo-check" in seen["argv"] and seen["argv"][-1] == "-"
    assert seen["stdin"] == nasty, "prompt must reach codex unchanged, via stdin"
    for bad in ("--dangerously-bypass-approvals-and-sandbox", "--full-auto", "workspace-write",
                "danger-full-access", "--trust"):
        assert not any(bad in x for x in seen["argv"]), bad

    rc, text, seen = call(["ask", "--repo", tmp], "q")
    assert rc == 0
    assert os.path.realpath(seen["cwd"]) == os.path.realpath(tmp)

    rc, text, seen = call(["resume", tid], "q")
    assert rc == 0 and seen["argv"][:3] == ["exec", "resume", tid] and has_fixed(seen["argv"])
    for bad_id in ("--last", "abc", tid + "x"):
        rc, text, seen = call(["resume", "--", bad_id], "q")
        assert rc == SKIPPED and seen is None and "not a UUID" in text, (bad_id, text)

    def skipped(rc, text, why):
        assert rc == SKIPPED and text.startswith("Codex: skipped (") and why in text, text
        assert text.count("\n") == 1 and len(text) <= 201, text

    skipped(*call(["ask"], "q", FAKE_RC="1")[:2], "exited 1")
    skipped(*call(["ask"], "q", stdout="")[:2], "no final message")
    skipped(*call(["ask"], "  \n")[:2], "empty prompt")
    skipped(*call(["ask"], "q", FAKE_LOGIN_RC="1")[:2], "not logged in")
    skipped(*call(["ask", "--repo", os.path.join(tmp, "nope")], "q")[:2], "not a directory")
    skipped(*call(["ask"], "q", PATH="/nonexistent")[:2], "not installed")
    long = skip_line(os.path.expanduser("~") + "/x\n" + "y" * 500)
    assert long.startswith("Codex: skipped (~/x y") and len(long) == 200, long
    rc, text, _ = call(["ask"], "q", stdout=events.replace(tid, "garbage"))
    skipped(rc, text, "no valid thread id")
    rc, text, _ = call(["ask"], "q", FAKE_RC="1", FAKE_ERR="user prompt secret\nreal error\n")
    skipped(rc, text, "real error")
    assert "secret" not in text

    # review, in a throwaway repo whose "origin/main" is a local branch
    repo = os.path.join(tmp, "repo")
    os.makedirs(repo)
    g = ["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
    subprocess.run(["git", "init", "-q", "-b", "main", repo], check=True)
    subprocess.run(g + ["commit", "-q", "--allow-empty", "-m", "base"], check=True)
    subprocess.run(g + ["switch", "-q", "-c", "work"], check=True)
    subprocess.run(g + ["commit", "-q", "--allow-empty", "-m", "head"], check=True)
    sha = lambda r: subprocess.run(["git", "-C", repo, "rev-parse", r], capture_output=True,
                                   text=True).stdout.strip()
    cwd = os.getcwd()
    os.chdir(repo)
    try:
        rc, text, seen = call(["review", "--base", "main"], stdout="looks fine\n")
        assert rc == 0, text
        assert text == f"Codex review of {sha('main')[:12]}..{sha('HEAD')[:12]}\nlooks fine\n", text
        assert seen["argv"][:3] == ["review", "--base", sha("main")] and has_fixed(seen["argv"])
        # remote base: fetched, resolved from FETCH_HEAD (no tracking ref exists here)
        subprocess.run(["git", "-C", repo, "remote", "add", "origin", repo], check=True)
        rc, text, seen = call(["review", "--base", "origin/main"], stdout="ok\n")
        assert rc == 0 and seen["argv"][2] == sha("main"), text
        skipped(*call(["review", "--base", "origin/nope"])[:2], "git fetch failed")
        skipped(*call(["review", "--base", "nope"])[:2], "rev-parse failed")
        with open(os.path.join(repo, "t.txt"), "w") as f:
            f.write("x")
        subprocess.run(g + ["add", "t.txt"], check=True)
        skipped(*call(["review", "--base", "main"])[:2], "uncommitted changes")
        subprocess.run(g + ["commit", "-q", "-m", "t"], check=True)
        skipped(*call(["review", "--base=--output=x"])[:2], "must be a ref")
        skipped(*call(["review", "--base", "main"], stdout="")[:2], "printed nothing")
        skipped(*call(["review", "--base", "main"], stdout="x", FAKE_RC="2")[:2], "exited 2")
        # HEAD moves while "codex" runs
        with open(fake) as f:
            src = f.read()
        with open(fake, "w") as f:
            f.write(src.replace("sys.stdout.write(", "import subprocess; subprocess.run(['git', "
                                "'-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', "
                                "'--allow-empty', '-m', 'moved']); sys.stdout.write("))
        skipped(*call(["review", "--base", "main"], stdout="x")[:2], "HEAD moved")
    finally:
        os.chdir(cwd)
        shutil.rmtree(tmp)
    print("codex: all checks pass")


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        self_test()
    else:
        sys.exit(main(sys.argv[1:]))
