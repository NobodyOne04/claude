#!/usr/bin/env python3
"""Claude's only way to call Codex: every call read-only, no approvals, no MCP (ADR 0008).

  codex.py ask [--repo DIR]            prompt on stdin; new thread
  codex.py resume THREAD_ID [--repo DIR]  prompt on stdin; continue a thread
  codex.py review [--base REF]         from the repo root; review the branch against REF
  codex.py docs --repo DIR             prompt on stdin; Codex proposes .md text (ADR 0009)
  codex.py docs-apply --repo DIR --sha256 HEX MANIFEST   write what `docs` checked
  codex.py --test                      self-check with a fake codex

Success prints `thread: <id>` (or the review header), then Codex's final message.
Any failure prints only `Codex: skipped (<reason>)` and exits 3.
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile

# Not overridable: the read-only guarantee lives here, not in the caller's command line.
FIXED = ["-c", 'sandbox_mode="read-only"', "-c", 'approval_policy="never"',
         "-c", "mcp_servers={}"]
# Built-in features whose tools act outside the sandbox: `apps` alone exposes ChatGPT
# connectors that deploy sites, change sharing and settings (seen on 0.172.0, 2026-11-25).
for _f in ("apps", "plugins", "remote_plugin", "browser_use", "browser_use_external",
           "computer_use", "image_generation", "skill_mcp_dependency_install", "tool_suggest",
           "hooks"):  # hooks run on the host, outside the sandbox
    FIXED += ["--disable", _f]
UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
SKIPPED, RERUN, REJECTED = 3, 4, 2


class Skip(Exception):
    """Codex unavailable or failed: record the skip line and carry on."""


class Rerun(Exception):
    """The review no longer matches the branch: fix what it says, then run it again."""


class Rejected(Exception):
    """Codex's docs proposal broke a rule: nothing was written."""


def skip_line(text):
    """The whole `Codex: skipped (...)` line, at most 200 chars, home shortened to ~."""
    text = " ".join(str(text).split()).replace(os.path.expanduser("~"), "~") or "no reason given"
    return f"Codex: skipped ({text[:200 - len('Codex: skipped ()')]})"


def run(cmd, stdin=b"", cwd=None):
    try:
        return subprocess.run(cmd, input=stdin, capture_output=True, cwd=cwd)
    except OSError as e:
        raise Skip(f"{os.path.basename(cmd[0])} could not start")  # no paths in PR text


CODEX = None  # absolute path, set once by preflight()


def ancestors(d):
    """d and every parent, as filesystem identities: on a case-insensitive Mac, `CLAUDE`
    and `claude` are the same directory, which no string comparison sees."""
    d, ids = os.path.realpath(d), []
    while True:
        try:
            st = os.stat(d)
            ids.append((st.st_dev, st.st_ino))
        except OSError:
            pass  # a PATH entry that doesn't exist: its parents still count
        parent = os.path.dirname(d)
        if parent == d:
            return ids, d
        d = parent


def repos_around(d):
    """Every repo containing d, nested ones included, found by looking for .git, not by
    running git, which would search the untrusted PATH. A non-repo d (like ~) adds none,
    so ~/.local/bin stays trusted."""
    found, d = [], os.path.realpath(d)
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            found.append(d)
        parent = os.path.dirname(d)
        if parent == d:
            return found
        d = parent


def preflight(repo=None, needs_codex=True):
    """Drop PATH entries that are relative or inside --repo or any repo around it or the
    cwd (an activated `.venv/bin`): the repo under review must not supply codex or git,
    which run with Claude's rights before any sandbox applies."""
    global CODEX
    untrusted = set()
    for r in repos_around(os.getcwd()) + ([repo] + repos_around(repo) if repo else []):
        try:
            st = os.stat(r)
            untrusted.add((st.st_dev, st.st_ino))
        except OSError:
            pass
    dirs = [d for d in os.environ.get("PATH", "").split(os.pathsep)
            if os.path.isabs(d) and not untrusted.intersection(ancestors(d)[0])]
    os.environ["PATH"] = os.pathsep.join(dirs)  # git and codex's children too
    if not needs_codex:
        return
    CODEX = shutil.which("codex")
    if not CODEX:
        raise Skip("codex not installed")
    if run([CODEX, "login", "status"]).returncode != 0:
        raise Skip("codex not logged in")


def last_message(stdout):
    """Thread id and final agent message from `codex exec --json` events."""
    thread, message = None, None
    # JSONL is split on LF only: splitlines() also breaks on U+2028 inside a JSON string
    for line in stdout.decode("utf-8", "replace").split("\n"):
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if not isinstance(ev, dict):
            continue
        thread = thread or ev.get("thread_id")
        item = ev.get("item")
        if ev.get("type") == "item.completed" and isinstance(item, dict) \
                and item.get("type") == "agent_message":
            text = item.get("text")
            # the last agent message is the answer; a blank one means no answer
            message = text if isinstance(text, str) and text.strip() else None
    return thread, message


def exit_reason(name, p):
    # fixed text only (stderr echoes the prompt), but say which known failure it was
    if b"usage limit" in p.stderr:
        return "codex usage limit reached"
    return f"{name} exited {p.returncode}"


def codex_exec(args, prompt, repo):
    if repo and not os.path.isdir(repo):
        raise Skip("--repo is not a directory")
    # outside a repo Codex refuses to start without this; it grants nothing
    cmd = [CODEX, "exec", *args, "--json", *FIXED, "--skip-git-repo-check", "-"]
    p = run(cmd, prompt, cwd=repo)
    if p.returncode != 0:
        raise Skip(exit_reason("codex", p))
    thread, message = last_message(p.stdout)
    if not message:
        raise Skip("no final message from codex")
    return thread, message


def ask(a, prompt):
    thread, message = codex_exec([], prompt, a.repo)
    if not UUID.fullmatch(str(thread)):
        raise Skip("no valid thread id from codex")
    return f"thread: {thread}\n{message}"


def resume(a, prompt):
    if not UUID.fullmatch(a.thread_id):
        raise Skip("thread id is not a UUID")
    thread, message = codex_exec(["resume", a.thread_id], prompt, a.repo)
    thread = thread or a.thread_id
    if not UUID.fullmatch(str(thread)):
        raise Skip("no valid thread id from codex")
    return f"thread: {thread}\n{message}"


def git(*args, cwd=None, stdin=b""):
    # no repo-configured hooks or fsmonitor: they would run on the host, with Claude's rights
    p = run(["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", *args],
            stdin, cwd=cwd)
    if p.returncode != 0:
        # fixed text: git's stderr can carry a remote URL with credentials, and this goes in PRs
        raise Skip(f"git {args[0]} failed")
    return p.stdout.decode("utf-8", "replace").strip()  # filenames needn't be UTF-8


def review(a, _prompt):
    if a.base.startswith("-"):
        raise Skip("base must be a ref")
    # codex reviews `git diff <base>`, which includes uncommitted edits: the header would lie
    if git("status", "--porcelain", "--untracked-files=no"):
        raise Rerun("uncommitted changes; commit them, then run the review again")
    remote, _, branch = a.base.partition("/")
    if branch and remote in git("remote").split():
        # git's own ref rules (no ':', '..', spaces...), and no leading '-' that fetch could
        # read as an option
        if branch.startswith("-") or run(["git", "check-ref-format",
                                          "refs/heads/" + branch]).returncode != 0:
            raise Skip("base branch name not allowed")
        # own ref per run: FETCH_HEAD or a tracking ref can be moved by a concurrent fetch
        ref = f"refs/codex-review/{os.getpid()}"
        git("fetch", "--quiet", "--no-tags", remote, f"+refs/heads/{branch}:{ref}")
        try:
            base = git("rev-parse", "--verify", ref + "^{commit}")
        finally:
            run(["git", "-c", "core.hooksPath=/dev/null", "update-ref", "-d", ref])
    else:
        base = git("rev-parse", "--verify", a.base + "^{commit}")
    head = git("rev-parse", "HEAD")
    p = run([CODEX, "review", "--base", base, *FIXED])
    # before reading the result: a changed branch must rerun even if codex failed
    if git("rev-parse", "HEAD") != head or git("status", "--porcelain", "--untracked-files=no"):
        raise Rerun("the branch changed during the review; run it again")
    if p.returncode != 0:
        raise Skip(exit_reason("codex review", p))
    text = p.stdout.decode("utf-8", "replace").strip()
    if not text:
        raise Skip("codex review printed nothing")
    return f"Codex review of {base[:12]}..{head[:12]}\n{text}"


DOCS_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["files"],
    "properties": {"files": {"type": "array", "minItems": 1, "items": {
        "type": "object", "additionalProperties": False, "required": ["path", "text"],
        "properties": {"path": {"type": "string"}, "text": {"type": "string"}}}}}}
DOCS_INSTRUCTION = """You are proposing documentation changes. You cannot write files.
Your final message must be exactly one JSON object and nothing else:
{"files": [{"path": "<path relative to the repo root>", "text": "<complete new content>"}]}
Only README.md files, .md files at the repo root, and .md files under docs/. Never
docs/adr/, never agent instruction files (SKILL.md, CLAUDE.md, AGENTS.md, GEMINI.md and
their variants), never anything under skills/, commands/, agents/ or a dot directory.
Give each file's complete new text.

The task:
"""
# they steer agents, so in this repo they are code (overrides and local variants included)
AGENT_FILES = {"skill.md", "claude.md", "claude.local.md", "agents.md", "agents.override.md",
               "gemini.md"}
INSTRUCTION_DIRS = {"skills", "commands", "agents"}  # plugin prompts are .md files too
MAX_TEXT = 200_000


def repo_root(repo):
    if not repo or not os.path.isdir(repo):
        raise Skip("--repo is not a directory")
    return os.path.realpath(git("rev-parse", "--show-toplevel", cwd=repo))


def tracked_as(root, path):
    """The index's exact spelling of `path`, or None: literal, NUL-delimited, unquoted."""
    p = run(["git", "--literal-pathspecs", "-c", "core.hooksPath=/dev/null",
             "-c", "core.fsmonitor=false", "ls-files", "-z", "--", path], cwd=root)
    names = p.stdout.decode("utf-8", "surrogateescape").split("\0")
    return names[0] if p.returncode == 0 and names[0] else None


def path_problem(root, path):
    """Why `path` may not be written by Codex, or None. Rules from ADR 0009."""
    if not isinstance(path, str) or not path:
        return "path is not a non-empty string"
    # same check as the text (paths print in the file list and diff), plus no tab or LF
    if hidden_char(path) or "\t" in path or "\n" in path or "\\" in path:
        return "path has a control, invisible or bidi character, or a backslash"
    if os.path.isabs(path):
        return "path must be relative"
    parts = path.split("/")
    if any(x in ("", ".", "..") for x in parts):
        return "path has an empty, '.' or '..' part"
    low = path.casefold()  # this Mac's disk is case-insensitive
    if not low.endswith(".md"):
        return "only .md files"
    if low.startswith("docs/adr/"):
        return "docs/adr/ stays with the owner and Claude"
    if parts[-1].casefold() in AGENT_FILES:
        return "agent instruction files (SKILL.md, CLAUDE.md, AGENTS.md...): Claude writes those"
    if any(x.startswith(".") for x in parts):
        return "nothing under a dot directory"
    full = root
    for x in parts:
        full = os.path.join(full, x)
        if os.path.islink(full):
            return "a part of the path is a symlink"
    if os.path.commonpath([root, os.path.realpath(full)]) != root:
        return "path leaves the repo"
    if os.path.lexists(full):
        st = os.lstat(full)
        if not stat.S_ISREG(st.st_mode) or st.st_mode & 0o111:
            return "existing target is not a plain, non-executable file"
        if tracked_as(root, path) != path:  # also catches readme.md standing in for README.md
            return "existing file is not tracked by git under exactly this name"
    # allowlist last: docs live in README.md files, root .md files and docs/
    low_parts = [x.casefold() for x in parts]
    if INSTRUCTION_DIRS.intersection(low_parts[:-1]):
        return "nothing under skills/, commands/ or agents/: those .md files are prompts"
    if not (len(parts) == 1 or low_parts[0] == "docs" or low_parts[-1] == "readme.md"):
        return "docs only: README.md files, .md files at the repo root, and docs/"
    return None


# The owner approves the diff in a terminal: these could make it show something other than
# what gets written (ANSI escapes, a bare CR rewinding the line, bidi overrides).
# bidi marks and overrides, line/paragraph separators, zero-width characters
INVISIBLE = (set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A))
             | {0x061C, 0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0x2028, 0x2029, 0x2060,
                0xFEFF})


def hidden_char(text):
    for i, c in enumerate(text):
        o = ord(c)
        if c == "\r" and text[i + 1:i + 2] == "\n":
            continue  # CRLF line endings are fine
        if (o < 0x20 and c not in "\n\t") or 0x7f <= o < 0xa0 or o in INVISIBLE:
            return f"U+{o:04X}"
    return None


def label(path):
    return repr(path)[:80]  # Codex-supplied text: bounded, quoted


def lf_lines(text):
    # LF only, endings kept: splitlines() would also split on U+2028 and eat CRs
    parts = text.split("\n")
    return [x + "\n" for x in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def unified(path, old, new):
    """The diff shown to the owner. Display only: docs-apply writes the text itself."""
    out = [f"--- {'/dev/null' if old is None else 'a/' + path}\n", f"+++ b/{path}\n"]
    for line in list(difflib.unified_diff(lf_lines(old or ""), lf_lines(new), n=3))[2:]:
        out.append(line if line.endswith("\n") else line + "\n\\ No newline at end of file\n")
    return "".join(out)


def read_text(full):
    """Current UTF-8 text of a file, line endings untouched; None if it doesn't exist."""
    if not os.path.exists(full):
        return None
    with open(full, "rb") as f:
        return f.read().decode("utf-8")  # UnicodeDecodeError: caller rejects


def sha(text):
    return None if text is None else hashlib.sha256(text.encode("utf-8")).hexdigest()


def docs(a, prompt):
    root = repo_root(a.repo)
    fd, schema = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(DOCS_SCHEMA, f)
        _, message = codex_exec(["--output-schema", schema],
                                DOCS_INSTRUCTION.encode() + prompt, root)
    finally:
        os.remove(schema)
    try:
        files = json.loads(message)["files"]
        assert isinstance(files, list) and files
    except (ValueError, KeyError, TypeError, AssertionError):
        raise Rejected(["the reply is not one JSON object with a non-empty files list"])
    problems, seen, plan, diff = [], set(), [], []
    for f in files:
        path, text = (f.get("path"), f.get("text")) if isinstance(f, dict) else (None, None)
        why = path_problem(root, path)
        if not why and path.casefold() in seen:
            why = "listed twice"
        if not why:
            try:
                if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_TEXT:
                    why = f"text is not a string of at most {MAX_TEXT} bytes"
            except UnicodeEncodeError:
                why = "text is not valid UTF-8"
        if not why and (bad := hidden_char(text)):
            why = f"text has a control, invisible or bidi character ({bad}) that would hide in the diff"
        if not why:
            try:
                old = read_text(os.path.join(root, path))
            except UnicodeDecodeError:
                why = "existing file is not UTF-8"
        if why:
            problems.append(f"{label(path)}: {why}")
            continue
        seen.add(path.casefold())
        if old != text:
            plan.append({"path": path, "old_sha256": sha(old), "text": text})
            diff.append(unified(path, old, text))
    if problems:
        raise Rejected(problems)
    if not plan:
        raise Rejected(["no file would change"])
    body = json.dumps({"repo": root, "files": plan}, sort_keys=True).encode()
    fd, out = tempfile.mkstemp(prefix="codex-docs-", suffix=".json")  # 0600
    with os.fdopen(fd, "wb") as f:
        f.write(body)
    return (f"repo: {root}\nmanifest: {out}\nsha256: {hashlib.sha256(body).hexdigest()}\n"
            + "".join(f"{'new ' if p['old_sha256'] is None else ''}{p['path']}\n" for p in plan)
            + "\n" + "".join(diff))


def docs_apply(a, _prompt):
    """Write the manifest's text, only if nothing changed since `docs` checked it."""
    root = repo_root(a.repo)
    try:
        with open(a.manifest, "rb") as f:
            body = f.read()
    except OSError:
        raise Skip("manifest not readable")
    if hashlib.sha256(body).hexdigest() != a.sha256:
        raise Rejected(["manifest changed since it was checked (SHA-256 mismatch)"])
    m = json.loads(body)
    if m["repo"] != root:
        raise Rejected(["manifest is for another repo"])
    problems = []
    for p in m["files"]:
        why = path_problem(root, p["path"])
        if not why:
            try:
                if sha(read_text(os.path.join(root, p["path"]))) != p["old_sha256"]:
                    why = "file changed since the proposal; run docs again"
            except UnicodeDecodeError:
                why = "file changed since the proposal; run docs again"
        if why:
            problems.append(f"{label(p['path'])}: {why}")
    if problems:
        raise Rejected(problems)
    for p in m["files"]:  # every check passed before the first write
        full = os.path.join(root, p["path"])
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="") as f:  # exact text, no translation
            f.write(p["text"])
    os.remove(a.manifest)
    return f"applied to {root}: " + ", ".join(p["path"] for p in m["files"])


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Skip("bad arguments")  # fixed: argparse would echo a mistyped prompt


def main(argv):
    ap = Parser(prog="codex.py")
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
    p = sub.add_parser("docs")
    p.add_argument("--repo", required=True)
    p.set_defaults(fn=docs, reads_prompt=True)
    p = sub.add_parser("docs-apply")
    p.add_argument("--repo", required=True)
    p.add_argument("--sha256", required=True)
    p.add_argument("manifest")
    p.set_defaults(fn=docs_apply, reads_prompt=False, needs_codex=False)
    try:
        a = ap.parse_args(argv)
        prompt = sys.stdin.buffer.read() if a.reads_prompt else b""
        if a.reads_prompt and not prompt.strip():
            raise Skip("empty prompt on stdin")
        preflight(getattr(a, "repo", None), getattr(a, "needs_codex", True))
        print(a.fn(a, prompt))
        return 0
    except Skip as e:
        print(skip_line(e))
        return SKIPPED
    except Rerun as e:
        print(f"Codex: rerun ({e})")
        return RERUN
    except Rejected as e:
        print("Codex docs: rejected, nothing written")
        for why in e.args[0]:
            print(f"- {why}")
        return REJECTED


def self_test():
    import contextlib
    import io
    import tempfile

    # the fixture's git must not touch the caller's repo (GIT_DIR, GIT_INDEX_FILE...) or use
    # its global config (commit signing, hooks)
    for k in [k for k in os.environ if k.startswith("GIT_")]:
        del os.environ[k]
    os.environ.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
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
    # ensure_ascii=False: a literal U+2028 in the final message, as Codex can send it
    events = "\n".join(json.dumps(e, ensure_ascii=False) for e in [
        {"type": "thread.started", "thread_id": tid},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "first"}},
        {"type": "item.completed", "item": {"type": "command_execution"}},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "fin\u2028al"}},
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
              "computer_use", "image_generation", "skill_mcp_dependency_install", "tool_suggest",
              "hooks"):
        want += ["--disable", f]

    def has_fixed(argv):
        # all the flags, in order, and no other -c that could override one
        return any(argv[i:i + len(want)] == want for i in range(len(argv))) and \
            argv.count("-c") == 3 and "--enable" not in argv

    nasty = "it's `rm -rf` \"$HOME\" $(x)\nline2\n"
    rc, text, seen = call(["ask"], nasty)
    assert rc == 0 and text == f"thread: {tid}\nfin\u2028al\n", text
    assert seen["argv"][:2] == ["exec", "--json"] and has_fixed(seen["argv"]), seen
    assert "--skip-git-repo-check" in seen["argv"] and seen["argv"][-1] == "-"
    assert seen["stdin"] == nasty, "prompt must reach codex unchanged, via stdin"
    for bad in ("--dangerously-bypass-approvals-and-sandbox", "--full-auto", "workspace-write",
                "danger-full-access", "--trust"):
        assert not any(bad in x for x in seen["argv"]), bad

    work = os.path.join(tmp, "work")
    os.makedirs(work)
    rc, text, seen = call(["ask", "--repo", work], "q")
    assert rc == 0
    assert os.path.realpath(seen["cwd"]) == os.path.realpath(work)

    rc, text, seen = call(["resume", tid], "q")
    assert rc == 0 and seen["argv"][:3] == ["exec", "resume", tid] and has_fixed(seen["argv"])
    for bad_id in ("--last", "abc", tid + "x", tid + "\n"):
        rc, text, seen = call(["resume", "--", bad_id], "q")
        assert rc == SKIPPED and seen is None and "not a UUID" in text, (bad_id, text)

    def skipped(rc, text, why):
        assert rc == SKIPPED and text.startswith("Codex: skipped (") and why in text, text
        assert text.count("\n") == 1 and len(text) <= 201, text

    skipped(*call(["ask"], "q", FAKE_RC="1")[:2], "exited 1")
    skipped(*call(["resume", tid], "q", stdout=events.replace(tid, "not-a-uuid"))[:2],
            "no valid thread id")
    skipped(*call(["resume", "--last"], "q")[:2], "bad arguments")
    skipped(*call(["nope"], "q")[:2], "bad arguments")
    rc, text, _ = call(["ask", "SENTINEL-PROMPT"], "q")
    skipped(rc, text, "bad arguments")
    assert "SENTINEL" not in text
    skipped(*call(["ask"], "q", stdout="")[:2], "no final message")
    skipped(*call(["ask"], "  \n")[:2], "empty prompt")
    skipped(*call(["ask"], "q", FAKE_LOGIN_RC="1")[:2], "not logged in")
    skipped(*call(["ask", "--repo", os.path.join(tmp, "nope")], "q")[:2], "not a directory")
    skipped(*call(["ask"], "q", PATH="/nonexistent")[:2], "not installed")
    # a relative PATH entry is ignored even when it holds a codex
    rel = os.path.relpath(os.path.dirname(fake))
    skipped(*call(["ask"], "q", PATH=rel)[:2], "not installed")
    # running from a non-repo dir that contains the codex install (like ~) still finds it
    cwd0 = os.getcwd()
    os.chdir(tmp)
    try:
        assert call(["ask"], "q")[0] == 0
    finally:
        os.chdir(cwd0)
    # --repo a subfolder of a repo whose .venv/bin holds codex: ignored, from outside too
    outer = os.path.join(tmp, "outer")
    os.makedirs(os.path.join(outer, ".git"))
    os.makedirs(os.path.join(outer, "sub"))
    venv = os.path.join(outer, ".venv", "bin")
    shutil.copytree(os.path.dirname(fake), venv)
    skipped(*call(["ask", "--repo", os.path.join(outer, "sub")], "q", PATH=venv)[:2],
            "not installed")
    alias = venv.replace(os.path.join(tmp, "outer"), os.path.join(tmp, "OUTER"))
    if os.path.exists(alias):  # case-insensitive volume (macOS default)
        skipped(*call(["ask", "--repo", os.path.join(outer, "sub")], "q", PATH=alias)[:2],
                "not installed")
    # an absolute entry inside --repo (an activated .venv) is ignored too
    skipped(*call(["ask", "--repo", tmp], "q", PATH=os.path.dirname(fake))[:2], "not installed")
    long = skip_line(os.path.expanduser("~") + "/x\n" + "y" * 500)
    assert long.startswith("Codex: skipped (~/x y") and len(long) == 200, long
    odd = "\n".join(json.dumps(e) for e in [
        {"type": "thread.started", "thread_id": tid},
        {"type": "item.completed", "item": "a string"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": {"x": 1}}},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "  "}}, [1]])
    skipped(*call(["ask"], "q", stdout=odd)[:2], "no final message")
    blank_last = events.replace('"fin\u2028al"', '""')
    assert blank_last != events
    skipped(*call(["ask"], "q", stdout=blank_last)[:2], "no final message")
    rc, text, _ = call(["ask"], "q", stdout=events.replace(tid, "garbage"))
    skipped(rc, text, "no valid thread id")
    rc, text, _ = call(["ask"], "q", FAKE_RC="1", FAKE_ERR="user prompt secret\nreal error\n")
    skipped(rc, text, "codex exited 1")
    assert "secret" not in text and "real error" not in text
    rc, text, _ = call(["ask"], "q", FAKE_RC="1",
                       FAKE_ERR="prompt\nERROR: You've hit your usage limit. Try at 10 PM\n")
    skipped(rc, text, "usage limit reached")
    assert "10 PM" not in text

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
        refs = subprocess.run(["git", "-C", repo, "for-each-ref", "refs/codex-review"],
                              capture_output=True, text=True).stdout
        assert refs == "", "per-run ref must be deleted"
        skipped(*call(["review", "--base", "origin/nope"])[:2], "git fetch failed")
        rc, text, _ = call(["review", "--base", "origin/release/v1+hotfix"])
        skipped(rc, text, "git fetch failed")  # a valid name gets as far as the fetch
        for bad in ("origin/-x", "origin/a:refs/heads/b", "origin/a..b", "origin/a b"):
            skipped(*call(["review", "--base", bad])[:2], "not allowed")
        assert sha("refs/heads/b") == "refs/heads/b"  # nothing was created
        skipped(*call(["review", "--base", "nope"])[:2], "rev-parse failed")
        with open(os.path.join(repo, "t.txt"), "w") as f:
            f.write("x")
        subprocess.run(g + ["add", "t.txt"], check=True)
        rc, text, _ = call(["review", "--base", "main"])
        assert rc == RERUN and text.startswith("Codex: rerun (uncommitted"), text
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
                                "'--allow-empty', '-m', 'moved'], check=True); sys.stdout.write("))
        rc, text, _ = call(["review", "--base", "main"], stdout="x")
        assert rc == RERUN and "changed during the review" in text, text
        rc, text, _ = call(["review", "--base", "main"], stdout="", FAKE_RC="1")
        assert rc == RERUN, ("a changed branch must rerun even when codex fails", text)
        # a tracked file edited (HEAD unchanged) while "codex" runs
        with open(fake, "w") as f:
            f.write(src.replace("sys.stdout.write(", "open('t.txt', 'a').write('y'); "
                                "sys.stdout.write("))
        rc, text, _ = call(["review", "--base", "main"], stdout="x")
        assert rc == RERUN and "changed during the review" in text, text
        with open(fake, "w") as f:
            f.write(src)  # the plain fake again

        # docs (ADR 0009): a throwaway repo with every kind of path the rules care about
        d = os.path.join(tmp, "docsrepo")
        gd = ["git", "-C", d, "-c", "user.name=t", "-c", "user.email=t@t",
              "-c", "commit.gpgsign=false"]
        subprocess.run(["git", "init", "-q", "-b", "main", d], check=True)
        for name, text in {"README.md": "old\n", "docs/guide.md": "g\n", "docs/x.sh": "x\n",
                           "docs/adr/0001-a.adr": "a\n", "docs/adr/README.md": "i\n",
                           "plugins/s/SKILL.md": "s\n", "CLAUDE.md": "c\n",
                           ".github/x.md": "h\n", "run.md": "r\n",
                           "real/inner.md": "n\n"}.items():
            os.makedirs(os.path.dirname(os.path.join(d, name)) or d, exist_ok=True)
            with open(os.path.join(d, name), "w") as f:
                f.write(text)
        os.chmod(os.path.join(d, "run.md"), 0o755)
        os.symlink("real", os.path.join(d, "linkdir"))
        os.symlink("README.md", os.path.join(d, "alias.md"))
        subprocess.run(gd + ["add", "-A"], check=True)
        subprocess.run(gd + ["commit", "-q", "-m", "init"], check=True)
        with open(os.path.join(d, "untracked.md"), "w") as f:
            f.write("u\n")

        def proposal(*files):
            msg = json.dumps({"files": [{"path": p, "text": t} for p, t in files]})
            return events.replace(json.dumps("fin\u2028al", ensure_ascii=False)[1:-1],
                                  msg.replace("\\", "\\\\").replace('"', '\\"'))

        for name, text in {"café.md": "c\n", "crlf.md": "a\r\nb\r\n"}.items():
            with open(os.path.join(d, name), "w", newline="") as f:
                f.write(text)
        subprocess.run(gd + ["add", "-A", "--", "café.md", "crlf.md"], check=True)
        subprocess.run(gd + ["commit", "-q", "-m", "more"], check=True)

        def manifest_of(text):
            return (text.split("manifest: ")[1].split("\n")[0],
                    text.split("sha256: ")[1].split("\n")[0])

        rc, text, seen = call(["docs", "--repo", d], "update the readme",
                              stdout=proposal(("README.md", "new\n"), ("docs/new.md", "hi"),
                                              ("plugins/p/README.md", "p\n"),
                                              ("café.md", "c2\n"),
                                              ("crlf.md", "a\r\nb\r\ncd\r\n")))
        assert rc == 0, text
        assert has_fixed(seen["argv"]) and "--output-schema" in seen["argv"], seen["argv"]
        assert seen["stdin"].endswith("update the readme") and "JSON" in seen["stdin"]
        assert "-old\n+new" in text and "new docs/new.md" in text, text
        assert text.count("\\ No newline at end of file") == 1, text  # only for "hi"
        man, digest = manifest_of(text)
        assert stat.S_IMODE(os.stat(man).st_mode) == 0o600
        assert open(os.path.join(d, "README.md")).read() == "old\n", "docs must write nothing"

        bad = {"x.py": "only .md", "docs/x.sh": "only .md", "GEMINI.md": "agent instruction",
               "sub/x.md": "docs only", "plugins/p/commands/x.md": "are prompts",
               "plugins/p/skills/s/README.md": "are prompts",
               "DOCS/ADR/0002.md": "docs/adr/", "docs/adr/README.md": "docs/adr/",
               "plugins/s/SKILL.md": "agent instruction", "CLAUDE.md": "agent instruction",
               "sub/agents.MD": "agent instruction", "AGENTS.override.md": "agent instruction",
               "CLAUDE.local.md": "agent instruction", ".github/x.md": "dot directory",
               "../x.md": "'..'", "/abs.md": "relative", "a\\b.md": "backslash",
               "a\nb.md": "control", "a\tb.md": "control", "a\u0085b.md": "control",
               "a\u202eb.md": "bidi", "a\u200fb.md": "bidi", "a\u200bb.md": "invisible",
               "linkdir/inner.md": "symlink", "alias.md": "symlink",
               "run.md": "non-executable", "untracked.md": "not tracked",
               "readme.md": "exactly this name"}
        for path, why in bad.items():
            if path == "readme.md" and not os.path.exists(os.path.join(d, "readme.md")):
                continue  # case-sensitive disk: readme.md is simply a new file there
            rc, text, _ = call(["docs", "--repo", d], "t", stdout=proposal((path, "x\n")))
            assert rc == REJECTED and why in text, (path, text)
        lone = events.replace("fin\u2028al",
                              '{\\"files\\": [{\\"path\\": \\"z.md\\", \\"text\\": \\"\\\\ud800\\"}]}')
        for reply, why in ((proposal(("a.md", "1"), ("A.md", "2")), "listed twice"),
                           (proposal(), "non-empty files list"),
                           (lone, "not valid UTF-8"),
                           (proposal(("README.md", "ok\u001b[2Khidden\n")), "U+001B"),
                           (proposal(("README.md", "shown\rhidden\n")), "U+000D"),
                           (proposal(("README.md", "a\u202eb\n")), "U+202E"),
                           (proposal(("README.md", "a\u0085b\n")), "U+0085"),
                           (proposal(("README.md", "a\u2028b\n")), "U+2028"),
                           (proposal(("README.md", "a\u200bb\n")), "U+200B"),
                           (proposal(("README.md", "a\u061cb\n")), "U+061C"),
                           (events.replace("fin\u2028al", "not json"), "not one JSON"),
                           (events.replace("fin\u2028al", 'Here: {\\"files\\": []}'),
                            "not one JSON"),
                           (proposal(("README.md", "old\n")), "no file would change")):
            rc, text, _ = call(["docs", "--repo", d], "t", stdout=reply)
            assert rc == REJECTED and why in text, (why, text)

        # docs-apply: refuses a changed manifest, another repo, a changed tree
        with open(man, "ab") as f:
            f.write(b" ")
        rc, text, _ = call(["docs-apply", "--repo", d, "--sha256", digest, man])
        assert rc == REJECTED and "SHA-256" in text, text
        os.remove(man)
        rc, text, _ = call(["docs", "--repo", d], "t",
                           stdout=proposal(("README.md", "new\n"), ("docs/new.md", "hi"),
                                           ("crlf.md", "a\r\nb\r\ncd\r\n")))
        man, digest = manifest_of(text)
        rc, text, _ = call(["docs-apply", "--repo", repo, "--sha256", digest, man])
        assert rc == REJECTED and "another repo" in text, text
        with open(os.path.join(d, "README.md"), "a") as f:
            f.write("edited meanwhile\n")
        rc, text, _ = call(["docs-apply", "--repo", d, "--sha256", digest, man])
        assert rc == REJECTED and "changed since the proposal" in text, text
        assert not os.path.exists(os.path.join(d, "docs/new.md")), "no partial writes"
        subprocess.run(gd + ["checkout", "--", "README.md"], check=True)
        rc, text, _ = call(["docs-apply", "--repo", d, "--sha256", digest, man],
                           PATH="/usr/bin")  # git, and no codex: docs-apply needs none
        assert rc == 0, text
        assert open(os.path.join(d, "README.md")).read() == "new\n"
        assert open(os.path.join(d, "docs/new.md")).read() == "hi"
        assert open(os.path.join(d, "crlf.md"), newline="").read() == "a\r\nb\r\ncd\r\n"
        assert not os.path.exists(man)
    finally:
        os.chdir(cwd)
        shutil.rmtree(tmp)
    print("codex: all checks pass")


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        self_test()
    else:
        sys.exit(main(sys.argv[1:]))
