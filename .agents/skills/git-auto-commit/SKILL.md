---
name: git-auto-commit
description: Analyze git status and diffs, group related changes into safe commits, stage files conservatively, and create clean commit history without interactive patching. Use when the user asks to commit code, submit current changes, auto-generate commit messages, split unrelated changes into multiple commits, or cleanly commit staged and unstaged work in a repository.
---

# Git Auto Commit

Use `references/git-commit-command.md` as the source reference for the original `/commit` command behavior that this skill was derived from.

## Worker Routing

Follow the shared dispatch, concurrency, safety, and review rules in `~/.codex/docs/workflows/harness-engineering.md`; this section maps only this skill's local phases.

- Prefer `luna_worker` with `Route: git-auto-commit/inspect` only for read-only repository inspection and diff grouping suggestions; it must not stage or mutate files.
- Keep staging, commit-message decisions, commits, pushes, and cleanup with the main agent.

## Inspect Repository State

- If the target directory is not a Git repository and the user asks to commit, run `git init` automatically before inspecting changes.
- After auto-initializing, verify `git config user.name` and `git config user.email` resolve. If either is missing, stop and ask the user to configure Git identity before committing.
- Do not set project-level Git identity during auto-init; rely on normal global Git config resolution.
- Run `git status --short`, `git diff --staged`, and `git diff` before deciding what to commit.
- Treat staged content as an intentional boundary when it already forms a coherent change.
- Ignore generated artifacts unless they are clearly required for the requested commit.

## Decide Commit Groups

- Split commits when files belong to different modules, behaviors, or business changes.
- Keep a mixed single file as one commit; do not try to split hunks out of one file.
- Merge small edits into one commit when they serve the same feature or fix and are easy to explain together.
- Prefer splitting commits when code changes are mixed with docs, generated deliverables, config-only changes, or unrelated module work.
- Prefer the smallest number of commits that still preserves clear history.

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
- Commit one logical group at a time, then rerun `git status --short`.
- Continue until the requested changes are committed or the remaining files are intentionally left out.
- Respect an existing staged set unless it is obviously broken and the user explicitly asks for regrouping.
- If the user also asks to push, inspect the current branch and remote first, then run `git push`.
- If push fails, report the exact error and keep the local commit intact.
- For commits with a body, use this safe sequence: write a temporary message file, `git commit -F <message-file>`, verify with `git log --format=%B -1 HEAD`, then remove the temporary file.

## Report Results

- Keep the commit report in plain text; do not use code blocks for the result summary.
- After each commit, report `✅ [模块/文件名] 提交成功: <标题>`.
- After all requested commits finish, report `🎉 所有变更处理完毕`.
- If anything is intentionally left uncommitted, say so explicitly.

## Grouping Heuristics

- Different module and different behavior: split into separate commits.
- Same module and same feature with small edits: merge into one commit.
- Same file with mixed logic: keep together and summarize primary and secondary changes.
- Mixed commit that is intentionally kept together: include a body explaining each secondary change.
- Subject-only commit: allowed only for one clear logical change.
- Existing staged content: treat as the current commit scope unless the user requests regrouping.
