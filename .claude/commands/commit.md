# /commit — Auto commit & push to this project's repo

## Repo config

```
REMOTE_NAME   : origin
REMOTE_URL    : https://github.com/radhika1290singh-design/a2-school.git
DEFAULT_BRANCH: main
GITHUB_USER   : radhika1290singh-design
GITHUB_PAT    : YOUR_PAT_HERE
```

---

## Behaviour

Run this fully automatically when the user types `/commit`. Do not ask for anything — no commit message, no confirmation, no input. Do it all and report back when done.

---

## Steps (run in order, no interruptions)

### 1. Verify repo
```bash
git remote -v
```
If the remote URL does not match `REMOTE_URL` above — STOP and tell the user. Do not proceed.

### 2. Stage all changes
```bash
git add -A
```

### 3. Check there is something to commit
```bash
git status --short
```
If output is empty — tell the user "Nothing to commit, working tree clean." and stop.

### 4. Auto-generate commit message
Run this to see exactly what changed:
```bash
git diff --cached --stat
git diff --cached
```
Write a concise, conventional-commit style message based on what you see in the diff:
- One subject line (max 72 chars): `type: short description`
- Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `style`, `test`
- Examples: `feat: add student enrollment API`, `chore: set up .claude folder structure`
- Do NOT mention file names in the subject unless they are the whole point of the change
- Do NOT ask the user — just generate it from the diff

### 5. Commit with generated message
```bash
git commit -m "<your generated message>"
```

### 6. Push (no credential prompts, no global config changes)
```bash
git push https://radhika1290singh-design:YOUR_PAT_HERE@github.com/radhika1290singh-design/a2-school.git main
```

### 7. Report back
Tell the user:
- The commit message that was used
- The branch pushed to
- Confirmation it succeeded (or the error if it failed)

---

## Safety rules (always enforce)

- **Never push if remote doesn't match config.** Stop and report mismatch.
- **Never force-push** unless user explicitly says "force push".
- **Never skip hooks** (`--no-verify`).
- **Never commit `.env` or `.env.*` files** (except `.env.example`).
- **Never run `git config --global` or touch any credential helper or shell config.**
