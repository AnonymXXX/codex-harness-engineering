# Global Agent Rules

## Code Review

For `/review`, `codex review`, and user-requested code reviews, write the final result in Chinese with this structure:

- `总结`: brief result.
- `问题`: findings ordered by severity with file/line references when available.
- `严重级别`: `高`, `中`, or `低` for every finding.
- `修改建议`: concrete fix for every finding.

Translate and reorganize raw reviewer output instead of returning English text. When no issue exists, state `未发现需要修复的问题`.

## Language And Replies

When the user writes in Chinese, or the conversation is mainly Chinese, use Chinese for progress updates and final summaries. Keep commands, paths, API names, package names, code symbols, and original errors unchanged.

## Skill Location

Keep user-managed skills under `~/.agents/skills`; reserve `~/.codex/skills` for Codex-managed system skills. After adding, removing, renaming, installing, copying, or migrating one, run `python3 ~/.agents/skills/harness-engineering/scripts/harness_doctor.py index --write` followed by `index --check`.

## Browser And Web Access

联网调研、网页读取、登录态操作、浏览器/CDP 控制和本地页面验证默认使用 `web-access`。只有它无法覆盖且用户明确同意时才使用可能切换 macOS 桌面的前台浏览器控制。任务结束时关闭自己创建的后台 tab，保留用户原有 tab。

## DESIGN.md And UI Consistency

For UI, frontend, styling, or visual-design work, read project-root `DESIGN.md` first when present. Otherwise infer the baseline from existing pages, components, and styles; do not invent a new visual language unless requested. When asked to create `DESIGN.md`, adapt `~/.codex/templates/DESIGN.md` to the existing UI first. Prefer established component conventions over a conflicting `DESIGN.md` and report the conflict.

## Risk-Based Execution

Classify risk before editing. Use the lightweight flow for clearly small, isolated work; follow `~/.codex/docs/workflows/git-worktree.md` for medium/large changes, shared behavior, configuration, generated artifacts, deployment, data, security, permissions, production operations, dirty state, or unclear blast radius. File count is a signal, not a fixed threshold.

State whether a task worktree is used before medium/large edits. If a qualifying task remains in the current worktree, explain the safety case and validation before committing, then continue without waiting unless a documented `Stop And Ask` condition applies.

## Destructive Operations

- Prefer `/usr/bin/trash` over permanent local deletion.
- Require explicit approval before permanent deletion, bulk overwrite, or Git operations that can discard commits, stashes, untracked files, or uncommitted changes.
- Never bypass a sandbox, approval prompt, or command rule through another tool or wrapper.
- Isolate unfamiliar repositories, bulk operations, and unattended agents.

## Git Worktree Workflow

For medium/large Git changes, use `~/.codex/docs/workflows/git-worktree.md`. Validated commit, eligible integration, current-task cleanup, and 7-day stale `codex/*` cleanup are autonomous completion steps. Never mix with user changes and stop on the workflow's `Stop And Ask` conditions.

Normal non-forced pushes to `origin/dev`, `origin/develop`, `origin/test`, and `origin/uat`, including known non-production CI or deployment effects, have built-in persistent authorization after project-required validation and integration preflight pass. A user-confirmed canonical project or domain policy may extend this only to an explicit repository allowlist and bounded existing non-production branches on `origin` under the same safeguards; see `~/.codex/docs/workflows/git-worktree.md`. A project rule or current-task instruction not to push overrides every persistent authorization. Other remotes, production targets or effects, tags, force pushes, and MR/PR creation or merge still require explicit authorization.

## Subagent Delegation

After risk classification, use Worker-first routing for every non-simple engineering task. Prefer `luna_worker` for bounded routine work and `terra_worker` for bounded Heavy Lane implementation; every routed `spawn_agent` call must set that exact `agent_type`, never the generic default. Common Skills own their stage routes. Follow `~/.codex/docs/workflows/harness-engineering.md` for thresholds, the structured dispatch and acceptance contract, the 8-thread pool, queueing, exclusions, leaf behavior, and main-agent review.

## Harness Engineering

Apply `~/.codex/docs/workflows/harness-engineering.md` implicitly to ordinary software work. Treat that workflow as the source of truth for risk, knowledge capture, and documentation maintenance; do not create or update durable project documents unless its Capture Gate passes. Keep this file limited to cross-project rules.

After Harness skill, workflow, template, or worktree-policy changes, run `python3 ~/.agents/skills/harness-engineering/scripts/harness_doctor.py doctor`; Doctor remains read-only.

@~/.codex/RTK.md
