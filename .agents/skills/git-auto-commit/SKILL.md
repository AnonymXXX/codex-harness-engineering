---
name: git-auto-commit
description: Analyze git status and diffs, group related changes into safe commits, stage files conservatively, and create clean commit history without interactive patching. Use when the user asks to commit code, submit current changes, auto-generate commit messages, split unrelated changes into multiple commits, or cleanly commit staged and unstaged work in a repository.
---

# Git Auto Commit

Use [message examples](references/git-commit-command.md) only when preparing a commit body. This skill governs commit grouping and message format; the global Git worktree workflow governs isolation, preflight, and push authorization.

## Inspect Repository State

- If the target directory is not a Git repository and the user asks to commit, run `git init` automatically before inspecting changes.
- After auto-initializing, verify `git config user.name` and `git config user.email` resolve. If either is missing, stop and ask the user to configure Git identity before committing.
- Do not set project-level Git identity during auto-init; rely on normal global Git config resolution.
- Run `git status --short`, `git diff --staged`, and `git diff` before deciding what to commit.
- Treat staged content as an intentional boundary when it already forms a coherent change.
- Ignore generated artifacts unless they are clearly required for the requested commit.

## Decide Commit Groups

- Group by user requirement and independently meaningful behavior, not by file type or directory. Code, tests, documentation, configuration, and required generated output for one requirement belong together.
- Keep unrelated requirements and user work separate; prefer the smallest number of coherent commits.
- Do not use `git add -p` or stage a mixed file wholesale. When task changes are attributable, reconstruct only those changes in a clean worktree from a verified base, or apply a reviewed non-interactive task patch to an isolated index. Check the resulting staged diff and preserve the original working file and any pre-existing staged boundary. Ask only when attribution, a required dependency, or the intended result remains unresolved.
- Respect an existing staged boundary when it forms a coherent authorized change.

## Converge One Requirement

- Default to one final content commit for the current user requirement and its continuous feedback. Small fixes, style adjustments, and review corrections for the same outcome belong in that commit.
- Do not interpret "one requirement" as "everything currently changed": unrelated requirements, independent business changes, and unrelated user work remain separate commits.
- Avoid creating a commit after every feedback round. Finish and validate a coherent requirement before its first publication whenever practical.
- If the requirement already has one unshared commit, amend it for later corrections when doing so is safe. If it has multiple unshared local checkpoint commits, squash them into one before the first push or MR/PR.
- After amend, squash, or rebase changes the tested commit, rerun the relevant validation and `git diff --check`.
- Treat a branch that already exists on a remote as shared. Never automatically rebase, amend, or force-push shared history; prefer MR/PR squash so the target receives one content commit. Require separate explicit authorization before `--force-with-lease`.
- Allow a platform-required merge commit, but keep only one content commit for the requirement. Never rewrite an already integrated target branch solely to clean old history.

## Stage Safely

- Prefer `git add <path>` or an explicit list of paths.
- Use `git add .` only when every changed file belongs to the same logical change.
- Never use `git add -p`.
- Use non-interactive git commands only.
- Never use destructive reset or checkout commands just to force a clean tree.

## Write Commit Messages

- Use one of these commit types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- Keep the type in English.
- Write the subject in Chinese, imperative, under 50 characters, with no period.
- When a body exists, the final commit message must be `subject`, then one blank line, then the bullet list body.
- Use a subject-only commit only when every staged file serves one clear change that the subject fully explains.
- A mixed commit MUST include a body. This includes multiple modules, multiple business behaviors, code plus docs, source changes plus generated deliverables, or config changes plus feature/fix work.
- If one file contains mixed logic, choose the dominant change as the subject and describe secondary changes in the body.
- If generated deliverables must be committed with source changes, describe both the source change and generated result in the body.
- Write the body in Chinese bullet lines when extra context is needed, with no blank lines between bullets.
- Put all body bullets in a single commit-message paragraph. Do not use one body `-m` flag per bullet, because Git will insert blank lines between paragraphs.
- Do not place the subject and body in the same `-m` argument in this workflow. Git can store it correctly if you manually include a blank line, but this pattern is too easy for the model to get wrong and accidentally omit the separator line.
- Never pass the literal characters `\n` inside normal quotes and assume Git will convert them to new lines; that will produce a broken one-line body containing backslash-n text.
- Default to `git commit -F <message-file>` whenever a body is needed. Treat inline `-m` construction as a fallback only when a message file is not practical.
- Build the message file with real line breaks, for example by writing `subject`, then a blank line, then the bullet lines.
- Before committing, preview the message and sanity-check that it contains actual line breaks, and that the second line is blank when a body exists.
- After committing with a body, run `git log --format=%B -1 HEAD` and verify the stored commit message still has the blank separator line; if not, immediately fix it with `git commit --amend -F <message-file>`.

## Execute Commits

- If the user clearly asks to commit changes, do not pause for confirmation.
- Commit one requirement-level logical group at a time, then rerun `git status --short`.
- Continue until the requested changes are committed or the remaining files are intentionally left out.
- Respect an existing staged set unless it is obviously broken and the user explicitly asks for regrouping.
- If the user also asks to push, follow [Git Worktree Workflow](../../../.codex/docs/workflows/git-worktree.md#remote-integration): inspect the target and task range, converge unshared commits, validate, and run integration preflight before an authorized push.
- If push fails, report the exact error and keep the local commit intact.
- For commits with a body, use this safe sequence: write a temporary message file, `git commit -F <message-file>`, verify with `git log --format=%B -1 HEAD`, then remove the temporary file.

## Report Results

Report each resulting commit hash and Chinese subject, validation, remaining changes, and actual local/remote state. Do not claim that all changes were handled when files were intentionally left out.
