# 4. Git & Version Control

## Q1. (Beginner) What is the difference between `git pull` and `git fetch`? When would you use fetch?

**Answer:**  
**fetch**: downloads **remote** refs and commits; **does not** merge. **pull**: fetch + **merge** (or rebase) into current branch. Use **fetch** when you want to **inspect** (e.g. `git log origin/main`) or **merge** later; use **pull** for a quick update. **Prefer fetch + merge/rebase** in scripts or when you want control.

---

## Q2. (Beginner) How do you undo the last commit but keep the changes in the working tree? How do you discard all local changes?

**Answer:**  
**Undo commit, keep changes**: `git reset --soft HEAD~1`. **Discard all local changes** (tracked): `git checkout -- .` or `git restore .`; **including untracked**: `git clean -fd` (use `-n` first to dry-run).

---

## Q3. (Beginner) What is a merge conflict? How do you resolve it?

**Answer:**  
**Conflict**: same lines changed in both branches; Git can’t auto-merge. **Resolve**: (1) Open conflicted files; fix markers (`<<<<<<<`, `=======`, `>>>>>>>`). (2) `git add` the files. (3) `git commit` (or continue rebase). **See conflict**: `git status`; **abort merge**: `git merge --abort`.

---

## Q4. (Beginner) What is the difference between `git merge` and `git rebase`? When would you avoid rebase?

**Answer:**  
**Merge**: creates a **merge commit**; history shows both branches. **Rebase**: replays your commits **on top** of target; linear history. **Avoid rebase** on **shared/public** branches (rewrites history, breaks others’ clones). Use **rebase** for local cleanup (e.g. before pushing feature branch).

---

## Q5. (Intermediate) How do you create a branch from a specific commit? How do you revert a single file to a previous commit?

**Answer:**  
**Branch from commit**: `git checkout -b new-branch <commit-hash>`. **Revert file**: `git checkout <commit-hash> -- path/to/file` (or `git restore --source <commit> path/to/file`). **Revert commit** (new commit that undoes): `git revert <commit-hash>`.

---

## Q6. (Intermediate) What is a Git hook? Name two useful hooks for CI/CD.

**Answer:**  
**Hook**: script in `.git/hooks/` that runs at events (commit, push, etc.). **pre-commit**: run **linter**/tests before commit; block if fail. **pre-push**: run **tests** or **security scan** before push. **Server-side**: **pre-receive** to enforce branch rules (e.g. reject force-push on main). Use for **quality** and **policy**.

---

## Q7. (Intermediate) Write the commands to squash the last 3 commits into one (with a new message) without merging.

**Answer:**  
`git reset --soft HEAD~3` then `git commit -m "New message"`. **Alternative**: `git rebase -i HEAD~3`; mark second and third as **squash** (or fixup); save; edit final message.

---

## Q8. (Intermediate) What is Git flow? What are the main branches and their purpose?

**Answer:**  
**main** (or master): production-ready. **develop**: integration for next release. **Feature** branches from develop; merge back to develop. **Release** branch from develop for release prep; merge to main and develop. **Hotfix** from main; merge to main and develop. **Alternative**: **trunk-based** (main only, short-lived branches).

---

## Q9. (Intermediate) How do you find which commit introduced a bug (e.g. "when did line 50 in app.js break")?

**Answer:**  
**git blame**: `git blame -L 50,50 app.js` (who changed that line). **Binary search**: `git bisect start`; mark known bad (e.g. HEAD) and known good (e.g. tag); `git bisect run ./test-script.sh` (Git checks out mid commits; script exits 0=good, 1=bad). **Log**: `git log -L 50,50:app.js` (history of that line).

---

## Q10. (Intermediate) What is `.gitignore` and what is a global ignore? How do you "unignore" a file that is ignored?

**Answer:**  
**.gitignore**: repo-level; listed paths are **untracked** and ignored. **Global**: `git config --global core.excludesfile ~/.gitignore_global`. **Unignore**: **remove** from .gitignore; if already tracked, **remove from index** first: `git rm --cached path` then commit. **Force add** (override ignore): `git add -f path` (not recommended for committed ignores).

---

## Q11. (Advanced) Production scenario: Someone force-pushed to main and overwrote commits that others had pulled. How do you recover the "lost" commits and prevent this in future?

**Answer:**  
**Recover**: **reflog** keeps previous HEADs: `git reflog` on a machine that had the old main; find commit hash; `git checkout -b recovered-main <hash>`; then `git push origin recovered-main` or reset main: `git push origin recovered-main:main --force` (coordinate with team). **Prevent**: **branch protection** (GitHub/GitLab): **disallow** force-push to main; require **PR** and **reviews**; **pre-receive** hook that rejects force-push.

---

## Q12. (Advanced) How do you set up a pre-commit hook that runs a linter and blocks the commit if it fails? Show a minimal script.

**Answer:**  
Create `.git/hooks/pre-commit` (or use **pre-commit** framework):
```bash
#!/bin/sh
npm run lint
exit $?
```
`chmod +x .git/hooks/pre-commit`. **With pre-commit framework**: `.pre-commit-config.yaml` with hooks (eslint, etc.); `pre-commit install`; runs in isolated env. **Stash** unstaged changes before running if hook expects clean working tree, or run only on staged files.

---

## Q13. (Advanced) What is a shallow clone? When would you use it in CI/CD?

**Answer:**  
**Shallow**: `git clone --depth 1 <url>`; only **latest** commit (no full history). **Use in CI**: **faster** clone; less disk; sufficient for **build** and **test**. **Limitation**: no history for blame/bisect; **fetch** more if needed: `git fetch --depth=100`. **Partial clone** (--filter=blob:none) is an alternative for large repos.

---

## Q14. (Advanced) How do you implement "deploy only when main has changed" in a pipeline (e.g. Jenkins)? What Git information do you use?

**Answer:**  
**Option 1**: **Poll** main (or webhook); **compare** previous commit to current (e.g. store last-built commit; if `git rev-parse HEAD` != stored, build and deploy). **Option 2**: **Webhook** on push to main; pipeline runs; **commit SHA** as build id. **Option 3**: **Path filter** (only deploy if certain paths changed). **Info**: **branch** (ref), **commit SHA**, **author**, **message**. Store **last-deployed** SHA in artifact or env; deploy only if new.

---

## Q15. (Advanced) Production scenario: You use trunk-based development. How do you enforce "no direct push to main; all changes via PR" and "main must be green (CI passing)"?

**Answer:**  
**Branch protection** (GitHub/GitLab/Bitbucket): (1) **Require PR** before merge to main; (2) **Require status checks** (CI) to pass; (3) **Require review** (e.g. 1 approval); (4) **Restrict** who can push/merge (or allow all with PR). **CI**: run on every push to main and on PR; **status** reported to Git; merge **blocked** until green. **Result**: main only updated via merged PRs that passed CI.

---

## Q16. (Advanced) What is Git submodule vs subtree? When would you use each?

**Answer:**  
**Submodule**: **pointer** to another repo (commit); cloned **separately**; parent tracks **commit** of submodule. **Use**: vendor or shared lib; **downside**: extra clone step, submodule can be detached. **Subtree**: **copy** of another repo merged into your tree; **single** clone; **downside**: history can be messy, updates are merge. **Use submodule** when you want **exact** version pinning and separate repo; **subtree** when you want one repo and don’t need to push back to the other repo easily.

---

## Q17. (Advanced) How do you do a code review (list of commits, diff) before merging a feature branch? What commands or workflow?

**Answer:**  
**Local**: `git fetch origin feature; git log main..origin/feature` (commits to review); `git diff main...origin/feature` (combined diff). **Platform**: **PR** (GitHub/GitLab) shows diff, comments, CI. **CLI**: `git diff main...feature --stat` then `git diff main...feature -- path` for specific files. **Best**: use **PR** with inline comments and CI.

---

## Q18. (Advanced) How do you clean up stale remote-tracking branches (e.g. after branches were deleted on origin)?

**Answer:**  
`git fetch --prune` (or `git remote prune origin`) removes remote-tracking refs for branches that no longer exist on origin. **Config**: `git config remote.origin.prune true` so every fetch prunes. **Delete local** branches that are gone on remote: script over `git branch -vv | grep ': gone]' | awk '{print $1}'` and delete (or use `git branch -d` after prune).

---

## Q19. (Advanced) Production scenario: A secret was committed and pushed to a repo. How do you remove it from history and rotate the secret?

**Answer:**  
(1) **Rotate** the secret **immediately** (in app, vault, etc.). (2) **Remove from history**: **BFG** or `git filter-repo --path secret.txt --invert-paths` (or replace with placeholder). (3) **Force-push**: `git push --force` (coordinate; everyone must re-clone or rebase). (4) **Prevent**: **pre-commit** hook (e.g. detect patterns); **secret scanning** (GitHub/GitLab); store secrets in vault, not repo.

---

## Q20. (Advanced) Senior red flags to avoid with Git

**Answer:**  
- **Force-push to shared** branches (main).  
- **Committing secrets** or large binaries without LFS.  
- **No branch protection** (anyone can push to main).  
- **Merging without CI** or review.  
- **Huge** or **unrelated** commits (hard to review and revert).  
- **Ignoring** merge conflicts (resolve properly).  
- **No .gitignore** for build artifacts and env files.

---

**Tradeoffs:** Startup: simple flow, maybe no hooks. Medium: branch protection, CI on PR. Enterprise: trunk-based or Git flow, mandatory review, secret scanning.
