---
name: commit-style
description: Write git commit messages in my style. Use whenever you are about to run `git commit` in any of my repos (zsh, nvim, tmux, claude, personal-ai, dotfiles), or when asked to write, fix or review a commit message.
---

# Commit style

## Subject line
- One line, at most ~72 characters, no trailing period.
- Says what changed in plain words. No Conventional Commits prefixes (`feat:`, `fix:`, `chore:`).
- When the change belongs to one area, lead with it and a colon:
  `gitleaks: ignore the revoked OpenAI key in early history`,
  `Prompt: the Mac look, with the Arch logo on Arch`, `Docs: terminal is kitty, not Ghostty`.
- When the commit does several things, list them with commas:
  `Go debugging, reload on outside edits, fix treesitter lock`.
- Never vague subjects like `Phase#1`, `update`, `wip`, `fixes`.

## ADR number: every commit except the initial one
- Start the subject with the ADR it falls under: `[ADR-0009] Runtime keys: encrypt at rest 🤖`.
- **Major change** (needs a decision record): write the new ADR with `adr-manager` and use
  its number: `[ADR-0011]`.
- **Minor change** (fix, docs, tweak): no new ADR file. Use the latest ADR number in the repo
  (highest in `docs/adr/`) plus a minor version, one higher than the last commit that used it:
  `git log --format=%s | grep -o '\[ADR-0010\.[0-9]*\]' | head -1` → `[ADR-0010.2]` becomes
  `[ADR-0010.3]`; none yet → `[ADR-0010.1]`.
- Repo without ADRs yet: `[ADR-0000.N]`, same minor counting.
- The initial commit has no ADR number.
- Count the tag in the ~72-character limit.

## Body
- Skip it for trivial changes where the subject says everything.
- Otherwise explain **why**, and what was wrong before, with concrete facts:
  "The old .zshrc appended a PATH line to itself on every shell start (3,182 copies)".
- Several changes: a `- ` bullet per change, prefixed with the file or area when useful
  (`- lib/git.zsh: ...`, `- make sync compiles the parsers ...`).
- Big commits can group bullets under short plain headings (`Look`, `Plugins`, `Fixes`).
- Name commits, keys, commands and files in backticks where it helps (`make sync`, `Alt-h`).
- If you tested the change, say how in one line: "Verified with an interactive session ...".
- Wrap at ~72 columns.

## Authorship: my name, plus a 🤖 marker
- Commit as me: the author and committer come from my git config (`user.name`, `user.email`,
  SSH signing). Never pass `--author`, never set `GIT_AUTHOR_*` / `GIT_COMMITTER_*`, never
  change git config.
- **No `Co-Authored-By` trailer** and no other Claude attribution lines, even if the session
  says to add one. This rule overrides that.
- Instead, end the **subject line** with a space and `🤖`, so I can spot your commits in
  `git log --oneline` and on GitHub:
  `Clipboard aliases: cbc copies, cbp pastes 🤖`
- Count the marker in the ~72-character limit.

## Git habits
- Never commit to `main`: work on a branch and open a PR, see `github-flow`.
- Commit or push only when asked. "commit and push" means both.
- A global gitleaks hook runs on every commit. Never bypass it with `--no-verify`;
  if it flags something, stop and show me.
- Stage only the files you changed for this task (`git add <paths>`), not `git add -A`.
- Pass the message with a heredoc (`git commit -F - <<'EOF'`) so formatting survives.
