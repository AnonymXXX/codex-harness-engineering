---
name: harness-engineering
description: "Choose risk-appropriate execution, worktree isolation, validation, and durable knowledge capture for software implementation and maintenance. Use for feature work, fixes, refactors, configuration, deployment, or explicit Harness/workflow tasks; keep small isolated edits lightweight."
---

# Harness Engineering

Use the lightest workflow that completes the user's intended task. Follow the global intent and authorization rules; this skill selects execution safeguards, not new permissions.

## Choose The Scope

Read the relevant project rules and inspect repository state. Distinguish a request for an answer, review, or diagnosis from a request to change something. Choose from the observed scope:

Prefer the main working directory in every lane. Create a worktree only when the Git workflow's necessity criteria are met; a larger or riskier task alone is not a reason. Reuse an already suitable task checkout when continuing work rather than moving it solely to follow this default.

- **Fast Lane:** a clear, cohesive local change in a safe worktree, without shared contracts/configuration, dependencies, generated artifacts, migrations, deployment, data, permissions, or security-sensitive behavior. File count alone does not decide risk.
- **Standard/Heavy Lane:** for broader work, read [Harness Engineering](../../../.codex/docs/workflows/harness-engineering.md) for proportional validation and conditional documentation capture. The lane alone does not require a plan, worktree, or extra skills.
- **Medium/large Git edits:** also read [Git Worktree Workflow](../../../.codex/docs/workflows/git-worktree.md). Resolve symlink targets before choosing the owning repository. Explain any necessary worktree before creating it; apply bootstrap only to a newly created checkout, and follow the commit and integration rules in either location.

Links above are relative to this repository's `.agents/skills/harness-engineering` directory; at runtime the same canonical documents are available under `~/.codex/docs/workflows/`.

## Fast Lane Contract

Inspect relevant code, make the scoped edit in the safe current worktree, and run `git diff --check` plus the narrowest useful existing lint/test and project-required checks. Add tests only for meaningful behavior or regression risk. Once checks pass, repeat or broaden them only for new changes, failures, or unresolved concerns. Avoid task worktrees, durable documents, plans, full builds, and global cleanup scans unless requested or evidence requires escalation.

Browser restrictions concern post-implementation acceptance: do not open pages/simulators, exercise UI, or run browser-driven suites unless explicitly requested or required by a higher-priority instruction. Research and explicitly requested browser operations remain allowed. Split mixed check commands and report omitted browser coverage. For UI reporting read the workflow's [Browser Acceptance](../../../.codex/docs/workflows/harness-engineering.md#browser-acceptance).

## Execution And Boundaries

Carry authorized work through implementation and validation; a proposal or offer to continue is not completion of a change request. Resolve routine choices from evidence and prepare reviewable results before requesting missing authority. Continue independent work while a necessary answer is pending.

A failed check calls for in-scope diagnosis and repair. A blocked operation does not block independent authorized work. Use [Stop And Ask](../../../.codex/docs/workflows/git-worktree.md#stop-and-ask) only for an unresolved boundary; the global rule owns how to explain a skill-caused pause.

For implementation work, finish with a scoped commit and eligible [Local Auto-Merge](../../../.codex/docs/workflows/git-worktree.md#local-auto-merge), unless the user's instructions exclude them. The Git workflow owns commit convergence, remote authorization, preflight, and cleanup. Execute separately authorized remote integration; validation alone grants no push or MR/PR permission.

Load the workflow's Capture Gate only for a durable-knowledge candidate or requested documentation work. Use a plan only when resumable state helps. Use subagents under global/runtime rules when a bounded independent task justifies coordination; no delegation quota applies. Keep inter-agent messages readable to humans.

## Specialist Routing

Use another skill only for a material task need, not a keyword or quota:

- `domain-modeling`: unresolved domain language or durable invariants.
- `codebase-design`: a non-trivial module/interface or test-seam decision.
- `tdd`: explicit test-first work or meaningful behavioral regression protection.
- `diagnosing-bugs`: a root cause requiring investigation beyond a localized fix.

## Validation And Reporting

After Harness changes, run `uv run ~/.agents/skills/harness-engineering/scripts/harness_doctor.py doctor`. For skill lifecycle changes or metadata-induced index drift, run its `index --write`, then `index --check`. Doctor is read-only; findings do not authorize unrelated repairs. Full/docs checks and periodic cleanup follow the workflow's conditional triggers.

Lead with the outcome, then the evidence and remaining limitations. For rule gardening, identify canonical files and validation. For UI changes, use the workflow's acceptance fields and actual integration state; omit empty boilerplate sections.
