---
name: harness-engineering
description: "Choose risk-appropriate execution, worktree isolation, validation, and durable knowledge capture for software implementation and maintenance. Use for feature work, fixes, refactors, configuration, deployment, or explicit Harness/workflow tasks; keep small isolated edits lightweight."
---

# Harness Engineering

Apply this workflow directly during software work; the user need not invoke a skill. Follow the runtime hierarchy and user authorization. Skill guidance neither overrides explicit user instructions nor grants external-action permissions.

## Choose The Scope

Classify the request using project rules, repository state, and the affected surface. Read only the references needed for that scope:

- **Fast Lane:** a clear, cohesive local change in a safe worktree, without shared contracts/configuration, dependencies, generated artifacts, migrations, deployment, data, permissions, or security-sensitive behavior. File count alone does not decide risk.
- **Standard/Heavy Lane:** for work beyond that boundary, read [Harness Engineering](../../../.codex/docs/workflows/harness-engineering.md) for risk lanes, proportionate checks, Capture Gate, and documentation maintenance.
- **Medium/large Git edits:** also read [Git Worktree Workflow](../../../.codex/docs/workflows/git-worktree.md). Resolve symlink targets before choosing the owning repository. State isolation before editing and use its bootstrap, commit, preflight, and cleanup rules.

Links above are relative to this repository's `.agents/skills/harness-engineering` directory; at runtime the same canonical documents are available under `~/.codex/docs/workflows/`.

## Fast Lane Contract

Inspect relevant repository state and code, edit in the safe current worktree, and run `git diff --check` plus the narrowest useful existing lint/test. Run additional project-required checks when applicable. Avoid task worktrees, durable documents, execution plans, full builds, and global cleanup scans unless requested or evidence requires escalation. A reversible copy/format edit does not need a new test that merely repeats its implementation.

Browser restrictions concern post-implementation acceptance: do not open pages/simulators, exercise UI, or run browser-driven suites unless explicitly requested or required by a higher-priority instruction. Research and explicitly requested browser operations remain allowed. Split mixed check commands and report omitted browser coverage. For UI reporting read the workflow's [Browser Acceptance](../../../.codex/docs/workflows/harness-engineering.md#browser-acceptance).

## Execution And Boundaries

Continue authorized work to completion. Resolve routine implementation choices from project evidence; ask only when missing information materially changes scope, data, security, or irreversible effects. Continue independent safe work while the answer is pending.

A failed check is evidence to diagnose and repair within scope. An unmet integration gate blocks integration, not authorized local implementation or validation. Consult [Stop And Ask](../../../.codex/docs/workflows/git-worktree.md#stop-and-ask) before an action whose authority or safety remains unresolved; production operations, data changes, secrets/permissions, destructive Git operations, and MR/PR actions retain their authorization requirements. If an applicable skill instruction causes a pause, identify its exact source and explain why existing authorization is insufficient.

For remote integration, the worktree workflow alone defines authorization, all seven High-confidence auto-integration gates, and preflight results. An explicit push request records browser acceptance as `passed`; commit-only leaves UI acceptance `pending`. Do not infer push or MR/PR authority from a check result. Keep unrelated changes isolated and retain blocked work for review.

Create durable documentation only for an explicit documentation request or when the workflow's Capture Gate passes. Create a resumable plan only when it materially helps larger or interruptible work. Subagent use follows global/runtime rules; no mandatory delegation protocol applies.

## Specialist Routing

Use another skill only for a material task need, not a keyword or quota:

- `domain-modeling`: unresolved domain language or durable invariants.
- `codebase-design`: a non-trivial module/interface or test-seam decision.
- `tdd`: explicit test-first work or meaningful behavioral regression protection.
- `diagnosing-bugs`: a root cause requiring investigation beyond a localized fix.

## Validation And Reporting

After Harness skill/workflow/template/worktree-policy changes, run `uv run ~/.agents/skills/harness-engineering/scripts/harness_doctor.py doctor`. After adding, removing, renaming, installing, copying, or migrating a user-managed skill, run its `index --write`, then `index --check`. Metadata changes that cause index drift also need an index refresh. Doctor is read-only; findings do not authorize unrelated repairs. The workflow owns optional full/docs checks and periodic stale cleanup.

Report changes, relevant evidence, and unresolved limits. For rule gardening, identify the canonical files and validation. For UI changes, include the workflow's acceptance fields and actual integration state. Avoid empty boilerplate status sections.
