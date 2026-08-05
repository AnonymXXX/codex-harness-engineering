---
name: harness-engineering
description: "Apply the user's Codex harness engineering workflow naturally for ordinary software work. Use when the user asks to build, implement, fix, modify, improve, continue, polish, refactor, migrate, complete, or troubleshoot a feature or project behavior; when a task may touch medium/large changes, shared behavior, configuration, generated artifacts, deployment, data, security, permissions, production operations, or unclear blast radius; or when the user explicitly mentions harness engineering, docs, rules, worktrees, validation, or execution plans."
---

# Harness Engineering

Use harness engineering as the governing workflow for safe, proportionate Codex work. In natural mode, the user does not need to name this skill; apply it quietly to normal feature, fix, and refactor requests.

## Source Of Truth

Classify the task from the request, project rules, repository state, and relevant code before loading detailed workflows.

- For a clear Fast Lane task, use this skill and the project's `AGENTS.md`; do not read the full Harness or worktree workflow unless evidence requires escalation. Do not reread the full Harness workflow after this Skill already supplies the active Fast Lane contract.
- For Standard or Heavy Lane work, read and follow `~/.codex/docs/workflows/harness-engineering.md`.
- For medium or large file-modifying work inside a Git repo, also read `~/.codex/docs/workflows/git-worktree.md`.

This skill routes to other skills; it does not replace the user's `AGENTS.md` rules.

## Risk Lanes

Use the Fast Lane when the request is clear, the change is cohesive and local, the worktree is safe, and the change does not affect shared contracts, shared configuration, dependencies, generated artifacts, migrations, deployment, data, permissions, or security-sensitive behavior. File count is only a signal; a cohesive three-file local fix can remain Fast Lane.

For Fast Lane work:

- inspect only the repository state and code needed to make the change;
- edit in the current worktree;
- run `git diff --check` plus the narrowest relevant lint or test;
- do not create a task worktree, durable document, execution plan, full build, browser session, or global stale-worktree scan unless the user explicitly requests it or evidence discovered during the task requires escalation.

Use the Standard Lane for cohesive local features and fixes that exceed the Fast Lane but do not touch high-risk surfaces. Use the Heavy Lane for medium or large changes, shared behavior, configuration, generated artifacts, releases, production operations, data, security, permissions, or unclear blast radius. File count is only a signal; risk and coupling decide the lane.

## Worker-first Coverage Gate

- After request and risk classification, route every safely delegable, bounded execution or evidence-gathering unit through an independent Worker, regardless of size, duration, or target count. Single-repository, single-page, single-source, and single-question inspection are included even when no files are modified.
- For a clear single-target read-only task, keep the main agent in a prerequisite-only phase limited to required Skill loading, risk classification, and the dispatch contract. The Worker is the primary evidence owner; after prerequisites, the next domain action is `spawn_agent`, not main-agent target inspection or tool discovery.
- Route bounded, independently verifiable execution to `deepseek_v4_flash_worker`. Common domain Skills own their stage-specific routes.
- Every routed `spawn_agent` call must set `agent_type` explicitly to `deepseek_v4_flash_worker` and use the workflow's auditable `route__<skill>__<phase>__<purpose>` task name; never use the generic default and label it afterward.
- Cross-provider dispatch to `deepseek_v4_flash_worker` uses `fork_turns = "1"` and writes the complete seven-field task into the parent context immediately before the `spawn_agent` call; `fork_turns = "none"` does not deliver the task reliably across providers.
- Put an itemized required-evidence checklist in `Verification`: name exactly what the Worker must inspect, the acceptable source or output for each item, and what counts as complete. Require `Verified` and `Gaps` to map back to that checklist.
- Keep each Worker write path exclusively owned until explicit release; use one same-Worker correction marked `Correction: 1/1`, and start unrelated work with a new spawn. The detailed lifecycle and interruption protocol lives in the linked workflow.
- When review finds missing required evidence, send only those gaps back to the same Worker before doing overlapping work in the main agent. After `followup_task`, snapshot status before waiting; never repeat `wait_agent` after a timeout without another status snapshot.
- For single-target read-only work and its correction, cap each `wait_agent.timeout_ms` at `10000` and cumulative waiting without useful progress at 30 seconds. Every newly spawned follow-on unit has its own one-correction budget.
- Use at most 8 direct Worker threads per root session. Workers are leaves and must not spawn, delegate, coordinate, or nest subagents.
- Every completed root turn that used a named Worker ends with `Worker 协议：version=10`; a same-Worker correction or invalid reuse also ends with `Worker 纠错：started=<n> completed=<n> failed=<n> violations=<n>`. Followup messages may be encrypted, so Doctor reconciles the unencrypted final marker; roots without v10 remain historical/informational.
- Preserve the existing conditional reports: a direct Worker interruption emits the exact `Worker 中断：...` line once; a root using `deepseek_v4_flash_worker` emits exactly one `Flash 验收：adopted=<n> partial=<n> rejected=<n> failed=<n>` line.
- When practical, split units expected beyond 30 minutes before dispatch; this is advisory, not a timeout or ordinary interruption reason.
- Structured dispatch, response and acceptance reporting, routing precedence, thresholds, eligible unit types, queueing, fork bounds, exclusions, parallel disjointness, and main-agent review/failure handling are defined in the [Harness workflow](../../../.codex/docs/workflows/harness-engineering.md).

## Natural Mode

- Do not ask the user to invoke `$harness-engineering` or another workflow skill for an ordinary request.
- For Fast Lane tasks, proceed directly in the current worktree and do not add ceremony beyond the narrow validation described above.
- Apply the Worker-first Coverage Gate and its detailed rules in `~/.codex/docs/workflows/harness-engineering.md`; keep risk classification, coordination, integration, review, and final reporting with the main agent.
- For clear medium-risk tasks, autonomously create a task worktree when the repo state and integration branch are safe and unambiguous, then run the worktree bootstrap from `~/.codex/docs/workflows/git-worktree.md` before editing.
- Treat validated commits, eligible merges, and cleanup of fully merged task worktrees and local task branches as normal autonomous completion steps. Do not wait merely because the user did not mention Git; stop only when the documented safety conditions require it.
- Record the target branch commit before creating a task worktree. Before remote integration, run the documented `integration_preflight.py` check with that task base against the latest remote target. Complete an authorized direct fast-forward autonomously; pause on `MR_REQUIRED` unless the user separately authorized the MR flow.
- For product or implementation choices with an obvious local default, choose the default, keep it in the conversation, and continue. Persist it only when the workflow's Capture Gate passes.
- Explore ordinary ambiguity directly and ask at most one blocking product question before execution unless the answer would materially change data, permissions, security, production behavior, or irreversible operations.
- When the user requests structured clarification, inspect the available context, separate confirmed facts from decisions, and ask only questions whose answers materially affect the implementation.
- When the user requests a handoff, directly provide a concise, resumable summary with current state, relevant paths or commits, validation, blockers, and the next concrete step.
- Explain visible safety actions at meaningful milestones. Do not narrate each rule read, search, lint transition, or routine command.
- Run the safe cleanup for stale `codex/*` worktrees only on the periodic cadence documented in the worktree workflow. Never run the global scan for a Fast Lane task.

## Workflow

1. Classify risk before editing.
2. Use a task worktree for medium/large repo changes unless a documented exception applies.
3. Implement and run the smallest credible validation for the changed surface.
4. When the task reveals a confirmed durable decision, project invariant, or evidenced repeat failure, apply the workflow's Capture Gate before writing documentation.
5. For larger or interruptible work, create or update an execution plan only when it will materially improve resumption.
6. Keep `AGENTS.md` short and link to detailed workflow docs instead of expanding it.

The capture criteria, document locations, conflict handling, and gardening policy live only in `~/.codex/docs/workflows/harness-engineering.md`. Ordinary tasks do not run a documentation audit or read Codex memory.

## Doctor And Templates

- Run `python3 ~/.agents/skills/harness-engineering/scripts/harness_doctor.py doctor` after changing Harness skills, workflows, templates, or worktree policy. This is the fast core check.
- Run `python3 ~/.agents/skills/harness-engineering/scripts/harness_doctor.py doctor --full` for periodic maintenance or when global skill metadata, runtime visibility, worktree debt, or session capture markers need inspection.
- Add repeatable `--section skills`, `--section worktrees`, or `--section sessions` to a full Doctor run when only selected groups are needed.
- Run the optional docs audit with `doctor --full --section docs --repo-root <repo>` only for document gardening; `docs` is not part of the default full scan.
- Run `python3 ~/.agents/skills/harness-engineering/scripts/harness_doctor.py index --write` after adding, removing, renaming, installing, or migrating user-managed skills, then run `index --check`.
- Treat `doctor` and `index --check` as read-only. Only `index --write` may update `~/.agents/skills-index.md`.
- When a project needs new Harness documents and has no established equivalent, start from `assets/project-harness/` and adapt the template instead of copying it unchanged.
- Doctor worktree findings are diagnostic only. Safe stale cleanup is a separate completion command: `python3 ~/.agents/skills/harness-engineering/scripts/harness_doctor.py cleanup --safe --older-than-days 7`. It may remove only eligible merged, clean, inactive, unlocked, unledgered `codex/*` worktrees; all uncertain states are preserved.

## Stop Conditions

Stop and ask before continuing when:

- risk is high or blast radius is unclear after reasonable exploration;
- the work may delete or rewrite user data, production data, permissions, secrets, or security-sensitive behavior;
- the work would push without current-task authorization, the built-in `origin/dev`, `origin/develop`, `origin/test`, and `origin/uat` authorization, or a qualifying user-confirmed project/domain authorization defined by the worktree workflow;
- the work would deploy or publish to production, migrate production data, or call external production systems;
- worktree bootstrap appears to require migrations, seeds, database resets, deploys, uploads, production service calls, or other external side effects;
- branch, worktree, or uncommitted-change state is ambiguous or unsafe;
- integration preflight returns `STOP` or `MR_REQUIRED`, requires force push, or cannot isolate the current task commits;
- validation fails and the safe next step is not obvious;
- multiple product directions are plausible and choosing one would likely cause rework.

## Routing

Do not route to another workflow skill merely because it could be helpful. Fast Lane work uses no additional workflow skill by default and at most one when its capability is essential. Standard Lane work also defaults to at most one domain skill; use more only when the user explicitly invokes them or each one independently covers a material part of the task.

- Durable terminology or invariants materially affect the task: use `$domain-modeling`; documentation writes still require the Capture Gate.
- Need non-trivial module/interface/seam design: use `$codebase-design`.
- Need regression protection for shared behavior or an existing test seam: use `$tdd`.
- Need root-cause investigation beyond a direct, localized failure: use `$diagnosing-bugs`.

## Final Reporting

When the task materially captures a rule, adds or changes an executable check, or gardens documentation, include a compact status such as:

`规则沉淀：<路径>；检查：<命令或路径>；文档整理：<已更新路径>。`

Do not emit a routine all-empty status line. Provide the audit result when the user explicitly asks for it.
