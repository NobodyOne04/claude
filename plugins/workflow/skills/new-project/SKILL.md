---
name: new-project
description: Start every new project with its own GitHub repo, so all work is backed up from the first commit. Use whenever I start a new project, app, tool, script collection or experiment, ask to "create/set up/scaffold/init" one, or when you're about to write code in a folder that isn't a git repo or has no GitHub remote.
---

# New project: repo first

Every project lives in a GitHub repo under my account `NobodyOne04` from the start. Nothing
worth keeping stays only on this disk.

## 1. Where and what
- Folder: `~/projects/<name>`, lowercase, hyphens. Repo name = folder name.
- If the folder or repo already exists (`gh repo view NobodyOne04/<name>`), stop and ask:
  reuse it, or pick another name. Never overwrite either.
- **Private** by default. Public only when I say so.
- If I didn't name the project, propose a name and a one-line description, then go on.

## 2. Create it
```
mkdir -p ~/projects/<name> && cd ~/projects/<name>
git init -b main
```
Add, and nothing more (the project itself comes later, through `github-flow`):
- `README.md`: `# <name>` and the one-line description.
- `CHANGELOG.md`: `# Changelog` and an empty `## Unreleased` (see `github-flow`).
- `CLAUDE.md`: the skeleton from `github-flow`, filled with what's known so far.
- `.gitignore` for the stack if it's known (`.DS_Store` always), plus `.env*`, so secrets
  never reach the backup.

First commit (`commit-style`): `Init <name> 🤖`.

## 3. Push it
```
gh repo create NobodyOne04/<name> --private --source . --remote origin --push --description "<one line>"
gh api -X PATCH repos/NobodyOne04/<name> -F delete_branch_on_merge=true
```
This is the one time something lands on `main` without a PR: an empty, new repo needs a
first commit to branch from. Only ever with `gh repo create --push` on a repo that had no
remote. Never use it to push later work.

Check: `gh repo view NobodyOne04/<name> --json visibility,defaultBranchRef` shows the
expected visibility and `main`, and `git status -sb` shows `main...origin/main`.

## 4. Then
- Real work starts on a branch, per `github-flow`.
- Give me the repo link and open it: `gh repo view --web`.
- Code I already have in a folder without a remote: same steps from 2, but commit the
  existing files after checking `git status` for secrets, keys, `.env` files and large
  build output; leave those out and say what you skipped.
