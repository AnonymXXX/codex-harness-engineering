# Harness Engineering

Use harness engineering as the default way to work across projects: choose proportionate execution safeguards and capture only durable knowledge that future work actually needs.

## Risk Lanes

Choose the lightest lane that safely covers the observed blast radius. Escalate when repository evidence contradicts the initial classification; do not escalate merely because a heavier check or another skill exists.

### Fast Lane

Use when the request is clear, the change is cohesive and local, the current worktree is safe, and the change does not affect shared contracts, shared configuration, dependencies, generated artifacts, migrations, deployment, data, permissions, or security-sensitive behavior. File count is only a signal; a cohesive three-file local fix can remain Fast Lane.

Inspect only the relevant state and code, edit in the current worktree, run `git diff --check`, and select the narrowest relevant lint or test. Do not create a task worktree, durable document, execution plan, full build, browser session, or global stale-worktree scan unless the user requests it or evidence requires escalation. Harness itself does not require a remote fetch before a local Fast Lane edit.

### Standard Lane

Use for cohesive local features and fixes that exceed the Fast Lane but do not touch Heavy Lane surfaces. Read the relevant workflow, use a task worktree when coupling, repository state, or likely interruption makes isolation useful, and validate affected behavior without automatically running every available check.

### Heavy Lane

Use for medium or large changes, shared behavior or contracts, configuration, generated artifacts, dependencies, migrations, releases, deployment, production operations, data, security, permissions, or unclear blast radius. Use the full worktree, documentation, validation, integration, and stop-condition workflow where applicable.

File count is a signal, not a hard boundary. A one-file security change is Heavy Lane; a cohesive three-file local fix can remain Fast Lane.

## Luna Worker Delegation

Luna scheduling is a coverage gate after risk classification, not an optional optimization. For every
non-simple engineering task, the main agent must classify the risk lane first and then proactively scan
the task graph for bounded Luna work units. A simple task is a clear, isolated one-step action whose
expected execution is below both of these thresholds; it may remain direct after the scan. When the
task is expected to require at least 2 substantive tool steps or to run longer than 60 seconds,
delegation is the priority before the main agent performs that eligible work.

### Work-unit coverage

Only dispatch a unit that is clear, repeatable, independently owned, and has an objective validation
or focused result inspection. The scan must consider, where applicable:

- codebase inventory, symbol/reference search, and file ownership mapping;
- API, schema, field, and other contract tracing;
- focused test authoring or test execution with isolated fixtures and outputs;
- read-only research, documentation inspection, and compatibility evidence gathering;
- a local implementation in an exclusively owned path or module; and
- independent verification of a result, diff, invariant, or focused check.

For Standard or Heavy Lane work, the main agent completes risk classification and any required worktree
bootstrap before dispatching independent units. A worker always operates in the selected task worktree,
never the original worktree by accident. The dispatch prompt names the exact scope, allowed paths,
owned state, expected output, and validation command.

### Scheduling and parallelism

At most 5 direct `luna_worker` instances may run concurrently. The main agent queues additional
eligible units until a slot is free; do not bypass the cap through nested or indirect workers. Parallel
units must have disjoint write paths, mutable state/resources, and validation ownership. Shared generated
outputs, fixtures, databases, ports, services, credentials, or validation commands count as overlap;
serialize the units when disjointness cannot be demonstrated before dispatch.

Use `fork_turns = "none"` by default. Use `fork_turns = "2"` only when the unit genuinely depends on
the immediately preceding turn and that context cannot be restated cheaply. Never use a full-history fork
or `fork_turns = "all"`; prompts must remain self-contained and bounded.

### Scope and exclusions

The main agent owns architecture, product, dependency, migration, and release decisions and all resulting
changes. It may delegate only side-effect-free evidence collection for those decisions, such as inventory,
contract tracing, documentation lookup, or compatibility checks; the worker must not choose, approve, or
execute the decision. Dangerous data operations, security behavior, permission changes, production
operations, and destructive actions are completely excluded from Luna delegation, even when a unit looks
small or has a read-only path. Direct edits to shared configuration, cross-module contracts, generated
artifacts, deployments, or other coupled surfaces remain with the main agent unless a separate bounded
read-only evidence unit is clearly isolated.

### Review and failure handling

The main agent owns coordination, conflict resolution, review, integration, final validation, and the
final answer. Treat every worker diff, artifact, and summary as untrusted until reviewed against its
scope and validation. If a spawn is unavailable or fails, make one correctly configured attempt only;
continue locally when safe or stop and report the blocker. Do not retry failed spawns or failed worker
validation in an automatic loop, and never report an unverified worker result as success.

## Validation Matrix

Choose the smallest set of checks that can credibly detect a regression in the changed surface. Do not duplicate equivalent checks merely for ceremony.

| Change surface | Default validation |
| --- | --- |
| Copy, simple condition, or formatting | `git diff --check` and target-file lint when available |
| Local behavior with an existing test seam | Focused test and target lint |
| Single-page UI layout or interaction | Target lint or component test; browser validation only when the material result cannot be established otherwise |
| Shared component, type, or API contract | Focused tests plus typecheck or the narrowest relevant build |
| Dependency, shared configuration, generated artifact, or build pipeline | Relevant full test/build path |
| Push, release, deployment, or production operation | Project-required validation and integration preflight |

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

Plan Mode, read-only analysis, and work that has not entered execution do not write project documentation. Ordinary tasks do not run a routine capture audit. Perform a lightweight audit only when the work actually surfaces a candidate durable decision, project invariant, or evidenced repeat correction.

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

Use `python3 ~/.agents/skills/harness-engineering/scripts/harness_doctor.py doctor` as the fast read-only core health check after changing Harness skills, workflow documents, templates, or worktree policy. It verifies Harness skill metadata and routing declarations, required files, and deterministic index drift without scanning repository worktrees or session history.

Use `python3 ~/.agents/skills/harness-engineering/scripts/harness_doctor.py doctor --full` for periodic maintenance or when diagnosing global Harness health. The full check also validates all skill metadata, checks runtime visibility, reports worktree lifecycle debt without changing it, and summarizes recent rule-capture markers. A rule-capture marker count is informational; tasks without a material rule or documentation change are not expected to emit an empty status line.

Full Doctor output is grouped into `Skills`, `Worktrees`, and `Sessions`. Use repeatable `--section skills`, `--section worktrees`, or `--section sessions` with `--full` to limit scanning and output. Session completion counts are deduplicated across log files by `turn_id`; `raw_completed` and `duplicates_skipped` keep the source volume visible.

Document gardening is an optional section and is not included in the default full scan. Run `python3 ~/.agents/skills/harness-engineering/scripts/harness_doctor.py doctor --full --section docs --repo-root <repo>` only when the documentation-gardening workflow calls for it.

After adding, removing, renaming, installing, copying, or migrating a user-managed skill, run:

```bash
python3 ~/.agents/skills/harness-engineering/scripts/harness_doctor.py index --write
python3 ~/.agents/skills/harness-engineering/scripts/harness_doctor.py index --check
```

`doctor` and `index --check` are read-only. Only `index --write` may update `~/.agents/skills-index.md`. A warning is informational in normal mode and fails under `doctor --strict`; errors always fail. Do not use Doctor findings as authorization to mutate project state.

Run `python3 ~/.agents/skills/harness-engineering/scripts/harness_doctor.py cleanup --safe --older-than-days 7` as periodic maintenance, not after every Git task. Never run it for Fast Lane work. For Standard or Heavy Lane completion, run it only when no successful global cleanup is known within the preceding 24 hours; when uncertain, skip the scan and leave it to the next periodic Harness maintenance pass. With no `--repo-root`, it scans only the current Git project; pass `--repo-root` repeatedly to include additional roots. Cleanup is fail-closed and restricted to stale, clean, merged, unlocked, unledgered, inactive `codex/*` worktrees. It never pushes; unsafe or unknown states are retained. Use `--dry-run` for manual inspection and diagnostics.

## Planning And Gardening

Create or update an execution plan only after execution begins and only when a larger, interruptible, or operational task materially benefits from resumable state. Do not persist a plan merely because it was discussed, because Plan Mode is active, or because the task is classified Standard or Heavy Lane.

For long-running or interruptible work, keep the execution plan usable as a progress ledger. It should link to the source product/spec requirement, record implementation status by work item, note blockers and decisions, list validation/deployment status, and leave concrete next steps or commands so a later session can resume without reconstructing the conversation.

For lingering task worktrees, keep a lightweight cross-task ledger in the integration or main worktree's execution-plan area or equivalent durable notes. The ledger exists so future sessions can discover unfinished task work from the main project entrypoint. If a dirty, unmerged, stale, or missing-on-disk worktree is discovered, inspect it read-only first and record its path, branch, status, changed-file summary, validation state if known, and recommended next step. Do not automatically delete, prune, reset, merge, or discard it unless the user explicitly asks or the standard worktree cleanup rules prove it is fully merged and clean.

Do not dirty the integration or main worktree only to record a ledger entry. If the current task created an isolated ledger or rule-documentation update and it can be staged by explicit path without mixing unrelated changes, commit that documentation update separately. This also applies when the integration or main worktree has unrelated local changes that are safe to leave alone. If the ledger update is not path-isolated, overlaps unrelated user changes, or cannot be committed safely, do not write it into the main worktree; include the proposed ledger entry in the final response and pause for user direction.

When validation fails but appears unrelated to the current change, record the exact failing command, the observed failure, why it is believed to be pre-existing or out of scope, whether it blocks the current task, and the recommended follow-up. Do not silently treat unrelated validation failures as success.

When changing durable docs or `AGENTS.md`, capturing a rule, closing an execution plan, or performing explicitly requested deep gardening, read and follow `~/.codex/docs/workflows/document-gardening.md`. Do not run this audit for an ordinary task with no documentation change or Capture Gate candidate, and do not read memory by default.

At the end of a task, mention rule capture, executable-check changes, or documentation gardening only when one of them materially changed. Use the user's conversation language and keep the note compact. Do not emit a routine all-empty status line. If the user asks for the audit result, report both changes and explicit no-change outcomes.
