# Harness Engineering

Use harness engineering as the default way to work across projects: choose proportionate execution safeguards and capture only durable knowledge that future work actually needs.

## Risk Lanes

This document is the complete reference. The harness-engineering Skill restates only the Fast Lane run-time contract so Fast Lane work does not need to read this file.

Choose the lightest lane that safely covers the observed blast radius. Escalate when repository evidence contradicts the initial classification; do not escalate merely because a heavier check or another skill exists.

### Fast Lane

Use when the request is clear, the change is cohesive and local, the current worktree is safe, and the change does not affect shared contracts, shared configuration, dependencies, generated artifacts, migrations, deployment, data, permissions, or security-sensitive behavior. File count is only a signal; a cohesive three-file local fix can remain Fast Lane.

Inspect only the relevant state and code, edit in the current worktree, run `git diff --check`, and select the narrowest relevant lint or test. Do not create a task worktree, durable document, execution plan, full build, or global stale-worktree scan unless the user requests it or evidence requires escalation. For post-implementation acceptance, do not start a browser session unless the user explicitly requests browser validation or a higher-priority instruction requires it. This does not restrict research or explicitly requested browser operations. Harness itself does not require a remote fetch before a local Fast Lane edit.

### Standard Lane

Use for cohesive local features and fixes that exceed the Fast Lane but do not touch Heavy Lane surfaces. Read the relevant workflow, use a task worktree when coupling, repository state, or likely interruption makes isolation useful, and validate affected behavior without automatically running every available check.

### Heavy Lane

Use for medium or large changes, shared behavior or contracts, configuration, generated artifacts, dependencies, migrations, releases, deployment, production operations, data, security, permissions, or unclear blast radius. Use the full worktree, documentation, validation, integration, and stop-condition workflow where applicable.

File count is a signal, not a hard boundary. A one-file security change is Heavy Lane; a cohesive three-file local fix can remain Fast Lane.

## Validation

Subagent use follows the global/runtime rules; no Worker protocol or fixed delegation quota applies.

Choose the smallest set of checks that can credibly detect a regression in the changed surface. Do not duplicate equivalent checks merely for ceremony.

For an explicitly requested model migration or behavior regression, use the optional [behavior scenarios](../../../.agents/skills/harness-engineering/evals/README.md). They consume model usage and do not run as part of Doctor or ordinary implementation checks. Distinguish actual fixture execution, policy decisions, and untested real-system behavior.

| Change surface | Default validation |
| --- | --- |
| Copy, simple condition, or formatting | `git diff --check` and target-file lint when available |
| Local behavior with an existing test seam | Focused test and target lint |
| Single-page UI layout or interaction | Target lint, component/unit tests, typecheck, or build; browser acceptance is not run by default and may be waived for eligible non-production integration |
| Shared component, type, or API contract | Focused tests plus typecheck or the narrowest relevant build |
| Dependency, shared configuration, generated artifact, or build pipeline | Relevant full test/build path |
| Push, release, deployment, or production operation | Project-required validation and integration preflight; explicit push requests and High-confidence auto-integration affect browser-acceptance state only, while other operations retain their separate authorization rules |

## Browser Acceptance

Continue to run proportionate non-browser validation by default, including relevant unit and integration tests, lint, typecheck, build, `git diff --check`, and static final-diff review. A build remains a non-browser check when it does not start a browser, simulator, visual comparison, or interactive acceptance flow. API and database integration tests also remain eligible when their existing data and external-system safeguards permit them.

This restriction applies to post-implementation acceptance, not to web research, authenticated web operations, or browser actions that are themselves explicitly requested task work. During acceptance, do not open local or remote pages, start simulators, exercise UI interactions, make visual judgments, or run browser-driven suites such as Playwright, Cypress, mini-program E2E, or screenshot regression unless the user explicitly requests browser validation or a higher-priority instruction requires it. When an aggregate command includes browser-driven checks, select the separable unit, integration, lint, typecheck, and build commands instead. If separation is not possible, skip the aggregate command and report exactly which browser coverage was omitted.

For UI-affecting work, the final report must separate `自动检查` from `浏览器验收`, then provide the target URL or entrypoint, prerequisites and test data, ordered actions and viewports, observable pass criteria, failure signals such as layout defects, console errors, or failed requests, and the current integration status. Without an integration basis, report `未执行，待人工验收`; after an explicit push request, report `未由 Agent 执行；用户明确要求推送，按规则视为通过`; after qualifying auto-integration, report `浏览器验收：未执行；满足高置信度自动集成条件，按策略豁免` and include the actual target and remote verification result.

A UI-affecting task may be implemented, validated with non-browser checks, and committed locally. An explicit current-task push request, including push-only or commit-and-push wording, counts as confirmation that browser acceptance passed; set the status to `passed`, record the task/thread source, and continue after normal validation and integration preflight. Do not ask separately whether acceptance was completed. A commit-only request leaves acceptance `pending`. This acceptance rule does not authorize production operations, tags, force pushes, other remotes, or MR/PR actions that require separate permission.

### High-confidence auto-integration

[Git Worktree Workflow](git-worktree.md#high-confidence-auto-integration) is the single source for all seven eligibility gates, target authorization, and preflight actions. An unmet gate blocks integration, not safe local work. Apply its full gate before recording `waived-by-high-confidence`; report the check results, static review, target, and remote verification. Never infer MR/PR permission from `MR_REQUIRED`.

## Documentation Shape

Keep each project's `AGENTS.md` short. It should be a map with entrypoints, source-of-truth links, meaningful boundaries, and concise deployment or validation notes. Do not let it become a large encyclopedia.

Keep the global `~/.codex/AGENTS.md` focused on highest-priority cross-project behavior. If a workflow becomes long or detailed, prefer moving the detailed procedure to a separate durable note such as `~/.codex/docs/workflows/<topic>.md` and keep only the governing rule and link in `AGENTS.md`.

Put durable project knowledge in structured `docs/` files. Prefer this structure for medium or large projects:
- `docs/product-specs/`: product requirements, business specifications, and user-visible behavior.
- `docs/engineering-rules/`: engineering constraints, business invariants, and rules agents must follow.
- `docs/exec-plans/`: execution plans, migration plans, release plans, and larger change plans.
- `docs/references/`: external references, research notes, and cited source material.

Adapt to the project instead of forcing structure mechanically:
- If a project already has an equivalent documentation structure, use and improve it.
- For small projects or one-off rules, `AGENTS.md` or a single `docs/engineering-rules.md` may be enough.
- Create the full recommended structure only when the project has enough long-lived product specs, engineering rules, execution plans, or references to justify it.
- When no equivalent document exists, start from the minimal templates under `~/.agents/skills/harness-engineering/assets/project-harness/` and adapt them to the project. Do not copy placeholders unchanged.

## Language Consistency

When the user writes in Chinese, or the current conversation is mainly Chinese, ordinary task progress updates and final summaries should be in Chinese. Avoid raw English template headings for completed work, changed files, validation, and manual verification. Keep commands, paths, API names, package names, code symbols, and original error text unchanged.

## Durable Knowledge Capture

This workflow is the single source of truth for automatic product/spec and engineering-rule capture. `AGENTS.md` and skills may link here but must not define competing capture criteria. A direct user request to create or edit documentation remains an ordinary task; automatic knowledge capture discovered while doing another task follows the gate below.

### Capture Gate

Create or update a durable product/spec or engineering-rule document only when all three conditions are true:

1. The content should remain true after the current session ends.
2. Upcoming implementation genuinely depends on the decision, or the rule prevents a repeated error supported by concrete evidence.
3. Current code, existing documentation, and user-confirmed direction contain no unresolved conflict about the content.

If any condition is false or unknown, keep the information in the conversation or current execution context. Do not write it as project truth.

Do not automatically capture:

- ordinary fixes, local implementation details, temporary debugging, or exploratory findings;
- one-off preferences, obvious facts already expressed by code, or routine validation results;
- unconfirmed options, proposals, or plans discussed only in conversation;
- documentation created only because a task is in Standard or Heavy Lane or touches a particular number of files;
- a conclusion that conflicts with an existing rule, spec, code path, or user instruction and has not been resolved.

Plan Mode, read-only analysis, and work that has not entered execution do not write project documentation. Use runtime-provided memory rules when memory is relevant; memory itself is not canonical project truth. Ordinary tasks do not run a routine capture audit. Perform a lightweight audit only when the work actually surfaces a candidate durable decision, project invariant, or evidenced repeat correction.

### Capture Scope

- Product behavior and operational decisions require explicit user confirmation and must be about to guide implementation, configuration, deployment, or operation. Otherwise leave them in the conversation.
- Engineering rules are limited to reusable project invariants or repeat corrections backed by a concrete failure, regression, or review history. A cross-project rule always requires explicit user confirmation before changing global documentation.
- Prefer the project's existing canonical document. If no suitable document exists, create at most one minimal file in the nearest established documentation location; do not generate the full recommended directory tree.
- When a confirmed decision replaces an older rule in the same scope, update or remove the old canonical wording so only one active rule remains. Git history preserves the old version. If replacement or scope is not explicitly resolved, stop automatic capture and report the conflict.
- Never store secrets, credentials, OAuth tokens, cookies, passwords, private keys, full sensitive URLs, raw confidential prompts, or private operational data. Use placeholders and non-sensitive metadata only.

When durable documentation is changed, follow `~/.codex/docs/workflows/document-gardening.md` to check the files in scope for canonical ownership, duplication, contradiction, and obsolete wording.

## Executable Checks

When a rule can be checked mechanically, prefer encoding it as a script, test, lint rule, CI check, or documented validation command instead of relying only on Markdown.

When an engineering rule passes the Capture Gate, explicitly decide whether a small executable check should also be added. Keep the check scoped, deterministic, and easy to run locally. If no check is useful, documentation alone is sufficient; explain the choice only when it materially affects the task or the user asks.

## Harness Health

Use `uv run ~/.agents/skills/harness-engineering/scripts/harness_doctor.py doctor` as the fast read-only core health check after changing Harness skills, workflow documents, templates, or worktree policy. The script's PEP 723 metadata supplies its Python version and PyYAML dependency. It verifies Harness skill metadata, required files, and deterministic index drift without scanning repository worktrees.

Use `uv run ~/.agents/skills/harness-engineering/scripts/harness_doctor.py doctor --full` for periodic maintenance or when diagnosing global Harness health. The full check validates all skill metadata, checks runtime visibility, and reports worktree lifecycle debt without changing it.

Full Doctor output is grouped into `Skills` and `Worktrees`. Use repeatable `--section skills` or `--section worktrees` with `--full` to limit scanning and output.

Document gardening is an optional section and is not included in the default full scan. Run `uv run ~/.agents/skills/harness-engineering/scripts/harness_doctor.py doctor --full --section docs --repo-root <repo>` only when the documentation-gardening workflow calls for it.

After adding, removing, renaming, installing, copying, or migrating a user-managed skill, run:

```bash
uv run ~/.agents/skills/harness-engineering/scripts/harness_doctor.py index --write
uv run ~/.agents/skills/harness-engineering/scripts/harness_doctor.py index --check
```

`doctor` and `index --check` are read-only. Only `index --write` may update `~/.agents/skills-index.md`. A warning is informational in normal mode and fails under `doctor --strict`; errors always fail. Do not use Doctor findings as authorization to mutate project state.

Run `uv run ~/.agents/skills/harness-engineering/scripts/harness_doctor.py cleanup --safe --older-than-days 7` as periodic maintenance, not after every Git task. Never run it for Fast Lane work. Use the cadence and eligibility rules in [Periodic Stale Cleanup](git-worktree.md#periodic-stale-cleanup); when the last run is unknown, skip the scan. With no `--repo-root`, it scans only the current Git project; pass `--repo-root` repeatedly to include additional roots. Cleanup is fail-closed and restricted to stale, clean, merged, unlocked, unledgered, inactive `codex/*` worktrees. It never pushes; unsafe or unknown states are retained. Use `--dry-run` for manual inspection and diagnostics.

## Planning And Gardening

Create or update an execution plan only after execution begins and only when a larger, interruptible, or operational task materially benefits from resumable state. Do not persist a plan merely because it was discussed, because Plan Mode is active, or because the task is classified Standard or Heavy Lane.

For long-running or interruptible work, keep the execution plan usable as a progress ledger. It should link to the source product/spec requirement, record implementation status by work item, note blockers and decisions, list validation/deployment status, and leave concrete next steps or commands so a later session can resume without reconstructing the conversation.

For lingering task worktrees, keep a lightweight cross-task ledger in the integration or main worktree's execution-plan area or equivalent durable notes. The ledger exists so future sessions can discover unfinished task work from the main project entrypoint. If a dirty, unmerged, stale, or missing-on-disk worktree is discovered, inspect it read-only first and record its path, branch, status, changed-file summary, validation state if known, browser acceptance state (`not-applicable`, `pending`, `passed`, or `waived-by-high-confidence`), the task/thread reference for any user confirmation or explicit push request, high-confidence evidence when applicable, and recommended next step. Do not automatically delete, prune, reset, merge, or discard it unless the user explicitly asks or the standard worktree cleanup rules prove it is fully merged and clean.

Do not dirty the integration or main worktree only to record a ledger entry. If the current task created an isolated ledger or rule-documentation update and it can be staged by explicit path without mixing unrelated changes, commit that documentation update separately. This also applies when the integration or main worktree has unrelated local changes that are safe to leave alone. If the ledger update is not path-isolated, overlaps unrelated user changes, or cannot be committed safely, do not write it into the main worktree; include the proposed ledger entry in the final response and pause for user direction.

When validation fails but appears unrelated to the current change, record the exact failing command, the observed failure, why it is believed to be pre-existing or out of scope, whether it blocks the current task, and the recommended follow-up. Do not silently treat unrelated validation failures as success.

When changing durable docs or `AGENTS.md`, capturing a rule, closing an execution plan, or performing explicitly requested deep gardening, read and follow `~/.codex/docs/workflows/document-gardening.md`. Do not run this audit for an ordinary task with no documentation change or Capture Gate candidate, and do not read memory by default.

At the end of a task, mention rule capture, executable-check changes, or documentation gardening only when one of them materially changed. Use the user's conversation language and keep the note compact. Do not emit a routine all-empty status line. If the user asks for the audit result, report both changes and explicit no-change outcomes.
