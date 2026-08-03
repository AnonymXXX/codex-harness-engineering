# Automated Git Worktree Workflow

Use this workflow for medium or large file-modifying tasks inside a Git repository.

## When To Use A Worktree

Use a task-specific worktree by default for medium or large changes, shared behavior, generated artifacts, configuration, deployment, data, security, permissions, production operations, or any unclear blast radius.

Do not create a task worktree for Fast Lane work: a clear change in one repository, typically no more than two files, with a safe current worktree and no shared contracts, shared configuration, dependencies, generated artifacts, migrations, deployment, data, permissions, or security-sensitive behavior. It is also acceptable to edit in the current worktree for other clearly small and low-risk changes when existing uncommitted changes are unrelated and will not be touched, or when the user explicitly asks for that.

File count alone does not determine risk: a one-file security change may require isolation, while a cohesive three-file local feature may not. Do not create a worktree solely because the task modifies code; use one when risk, coupling, repository state, or likely interruption justifies isolation.

Always inspect worktree state first and avoid touching unrelated uncommitted changes.

## Before Editing

- If the current directory is not already a task-specific worktree, create a new worktree from the repository's integration branch.
- Determine the integration branch in this order: project `AGENTS.md` or documented project rule, the current branch's upstream integration branch, `origin/HEAD`, then common integration names such as `main`, `master`, or `develop`. If it is still ambiguous, ask the user before continuing.
- Before creating the task worktree, confirm the original worktree is clean or that any existing uncommitted changes are unrelated and will not be touched.
- Record the integration branch commit as the immutable task base before creating the task worktree. Keep that OID available for remote preflight and safe local synchronization.
- Use a descriptive task branch name, such as `codex/<task-slug>`.
- Place the worktree in a sibling directory, such as `../<repo-name>.worktrees/<task-slug>`.
- Do all implementation, edits, and validation inside that worktree.
- Treat this section as a checklist: inspect status, determine the integration branch, create the task worktree, switch into it, implement there, validate there, commit there when appropriate, then merge back only under the rules below.
- If the task meets the worktree criteria but you intentionally do not use a task worktree, record the exception before editing and again in the final response.

## Worktree Bootstrap

After creating a task worktree, prepare that worktree before editing:

- Immediately switch all subsequent commands, file reads, edits, patches, tests, and builds to the task worktree's absolute path. Do not keep operating from the original worktree.
- Record or restate the task worktree path in the working notes before the first edit.
- Run `python3 ~/.agents/skills/harness-engineering/scripts/worktree_bootstrap.py <absolute-worktree-path>` automatically before the first edit.
- The bootstrap runs an executable project `scripts/bootstrap-worktree.sh` first when present. Otherwise it uses `package.json#packageManager` or one unambiguous lockfile to select `pnpm install --frozen-lockfile`, `npm ci`, `yarn install --immutable`, or `bun install --frozen-lockfile`.
- Multiple package-manager lockfiles without a declaring `packageManager`, a declared manager without its lockfile, invalid metadata, or a failed command stops bootstrap. A non-Node worktree with no project hook is a successful no-op. Use `--dry-run` to inspect the selected command.
- Run only non-destructive, project-documented preparation commands that local tests or builds require, such as type/shared package builds, Prisma/client generation, GraphQL/OpenAPI/protobuf codegen, or other generated-type commands.
- Do not automatically run migrations, seeds, database resets, deploys, uploads, production service calls, or commands that modify external state. Ask first when preparation appears to require any of these.
- If bootstrap fails, diagnose the environment or dependency issue before editing code. Do not treat missing dependencies or generated artifacts as application failures.
- If any edit or patch accidentally lands in the original worktree, stop implementation, move the intended change into the task worktree, and restore the original worktree without using destructive checkout/reset commands unless explicitly requested.

## Long-Running Worktree Ledger

When a task worktree remains unmerged or dirty beyond the current session, record a short status ledger in the integration or main worktree's execution-plan area or equivalent durable notes. The ledger belongs to the cross-task project entrypoint by default, not only to the feature worktree, so future sessions can discover unfinished task work from main.

Each ledger entry should include:

- worktree path and branch;
- intended task or feature;
- current state, such as clean, dirty, committed but unmerged, stale, or missing on disk;
- concise changed-file summary from `git status --short` or `git diff --stat`;
- latest validation result if known;
- concrete next step, such as continue, review, commit, merge, clean up, or ask the user.

If you discover an existing dirty or stale task worktree, inspect it read-only and record the status before taking action. Do not automatically delete, prune, reset, merge, or discard a lingering worktree unless the user explicitly asks or the worktree is proven fully merged and clean under the cleanup rules below.

Do not leave the integration or main worktree dirty just to record ledger status. If the current task created a ledger or rule-documentation update that is path-isolated, stage it by explicit path and commit it separately, even when unrelated local changes exist elsewhere in the integration or main worktree. Mark that commit in the working notes as a Harness-created docs-only commit. If the ledger update is not path-isolated or overlaps unrelated user changes, do not write it; include the proposed ledger text in the final response instead.

## After Completing The Task

- Run the relevant validation commands.
- If validation passes, automatically commit small low-risk implementation changes with a concise commit message unless the task is exploratory, temporary, explicitly marked no-commit, or the user asks to inspect the diff first.
- For medium or large changes, briefly summarize the diff and validation result before committing, then continue without waiting unless the user asked to inspect the diff first or a stop condition applies.
- Treat validated commit, eligible integration, post-integration validation, and cleanup as the normal autonomous completion path. Do not ask for confirmation merely because the user did not explicitly request local Git operations.
- Before committing a medium or large change that was made in the current worktree, explain why skipping a task worktree is still safe, what validation passed, and whether unrelated user changes could be mixed in. Continue without waiting unless a `Stop And Ask` condition applies.
- Keep local-target maintenance separate from remote integration. A divergent local `uat`, `main`, or other integration branch is not evidence that the remote target requires an MR and must not block an otherwise safe remote fast-forward.
- A local integration branch may be fast-forwarded when it is clean, still points to the recorded task base, and can accept the validated result with `--ff-only`. It does not need to match its upstream. If it moved or contains user changes, skip local synchronization and preserve user state without blocking an independently safe remote integration.
- Run the relevant validation again after any rebase or integration that changes the tested commit.
- After remote integration, fetch the target again and verify the integrated task commit is its ancestor. Synchronize a safe local target when eligible, then remove the merged task worktree and local task branch unless the user asked to keep them. If the local target moved or contains user changes, skip only local synchronization; remote containment still proves the current task branch is safe to clean up.

## Periodic Stale Cleanup

Do not run the global cleanup scan for Fast Lane work. For Standard or Heavy Lane completion, run `python3 ~/.agents/skills/harness-engineering/scripts/harness_doctor.py cleanup --safe --older-than-days 7` only when no successful global cleanup is known within the preceding 24 hours. When uncertain, skip it and leave cleanup to the next periodic Harness maintenance pass.

Cleanup automatically removes only stale `codex/*` worktrees that are clean, fully merged into their integration branch, unlocked, not ledgered, and unused as any process cwd. Age is the newest of directory creation time, directory modification time, and branch commit time. Dirty, unmerged, detached, non-Codex, unknown, active, locked, and ledgered worktrees are retained. Cleanup failure is reported and leaves uncertain worktrees untouched; it does not retroactively invalidate completed implementation work.

## Remote Integration

Remote integration uses the latest remote target as its source of truth. It does not require checking out, repairing, or merging through a local target branch.

Normal non-forced updates to `origin/dev`, `origin/develop`, `origin/test`, and `origin/uat` have built-in persistent authorization after project-required validation and preflight pass. This authorization includes known non-production CI and deployment effects triggered by those branch updates.

A user-confirmed canonical project or domain policy may persistently authorize additional non-production targets only when it:

- identifies an explicit repository allowlist and bounded branch names or patterns;
- applies only to existing branches on `origin`, normal non-forced pushes, and known non-production CI or deployment effects;
- requires project-defined validation and the same integration preflight;
- excludes branch names containing `main`, `master`, `release`, `prod`, or `production` as a complete segment separated by the start, end, `-`, `_`, or `/`;
- does not authorize tags, force pushes, MR/PR creation or merge, production effects, or another remote.

A project rule or current-task instruction such as "do not push" overrides every persistent authorization. A project policy may narrow the built-in authorization without meeting the extension requirements above; it may expand authorization only under those requirements.

1. Read project rules before choosing an integration mode. Pass `--integration-mode mr-required` only when the project explicitly requires an MR/PR, review, or platform checks before target updates. A rule that says not to commit directly on the target still permits fast-forwarding commits created on a task branch unless it also forbids direct pushes.
2. Run the read-only preflight from the clean task worktree:

   ```bash
   python3 ~/.agents/skills/harness-engineering/scripts/integration_preflight.py \
     <task-worktree> --task <task-branch> --target <target-branch> \
     --task-base <recorded-target-oid> --remote origin --integration-mode auto
   ```

   Automatic push preflight must include `--task-base`. The command fetches the remote target and returns one of `ALREADY_INTEGRATED`, `DIRECT_FF`, `REBASE_THEN_FF`, `MR_REQUIRED`, or `STOP`. JSON output includes `task_base_oid`, whether baseline checks ran as `baseline_checked`, and any `extra_commits` found in `<remote>/<target>..<task-base>`. It returns `STOP` when the task base is not a task ancestor, contains commits absent from the latest remote target, has unrelated or unsafely rewritten history, or cannot identify the current task range. Action classification never grants push authorization. Use `--format json` for machine-readable output. Use `--no-fetch` only in controlled tests or after an independently verified fetch.
3. Handle the result deterministically:
   - `ALREADY_INTEGRATED`: verify the remote ancestry and continue with validation and cleanup.
   - `DIRECT_FF`: when push is authorized, run a normal non-forced `git push origin <task-branch>:<target-branch>`. This applies to any target branch that project policy and the server permit; branch names alone do not force an MR.
   - `REBASE_THEN_FF`: for an unshared task branch, run `git rebase --onto origin/<target-branch> <task-base> <task-branch>` so only current-task commits are replayed. Rerun validation and preflight before push. Never rebase a shared task branch.
   - `MR_REQUIRED`: pause and report it. Persistent non-production push authorization does not authorize creating an MR/PR; follow the MR flow below only after separate user authorization.
   - `STOP`: report the reason and do not integrate.
4. Classify a failed direct push instead of guessing:
   - On non-fast-forward rejection, fetch and rerun preflight against the new remote target. Revalidate after any resulting rebase. Stop if target movement repeatedly prevents a stable update.
   - On an explicit protected-branch or MR-only rejection, report `MR_REQUIRED` and pause. Enter the MR flow only after separate user authorization.
   - On authentication failure, missing permission, unknown hook rejection, or transport failure, stop and report the exact error. Do not assume an MR will bypass it.
5. After a direct push, fetch the target, verify the integrated task commit is its ancestor, and run the applicable post-integration validation. Fast-forward a clean local target only if it still points to the task base, then remove the merged current-task worktree and branch. Skip unsafe local synchronization without touching user state.

### MR Flow

- An authorization to "push and merge" covers pushing the current task branch, creating its MR/PR, merging it, and deleting the merged current-task source branch. Push-only authorization does not authorize creating or merging an MR.
- Use the project's configured provider workflow. For GitHub platform objects use `github-cli-ops`; for GitLab use the established authenticated CLI or `web-access` path without bypassing platform policy.
- Wait for required automated checks when they exist. If human approval is required, leave the MR open and report that blocker rather than approving on someone else's behalf.
- When checks pass and no human approval is required, merge automatically using the repository's configured merge method. If the required platform flow only offers a merge commit, the configured merge method counts as project permission when the user already authorized push and merge; report the resulting merge commit.
- Verify the task commit is contained in the remote target after merge, then delete the merged current-task remote branch when the platform has not already done so and complete normal local cleanup.
- Release, publication, deployment, migration, and production-operation workflows retain their own stricter rules. If updating a branch is known to trigger one of those side effects, obtain the corresponding authorization in addition to push and merge authorization.

## Stop And Ask

Stop and ask the user before continuing if:

- The target integration branch is ambiguous.
- The original worktree has uncommitted changes that might be touched by the task.
- The task worktree contains uncommitted changes not created by the current task.
- Validation fails.
- Rebase or merge conflicts occur.
- Remote preflight returns `STOP`, target movement repeatedly prevents a stable update, or the remote target is ambiguous.
- Integration would require force push, reset, rebasing a shared branch, deleting unmerged work, or bypassing required platform approval.
- A remote push is required but neither current-task authorization nor the persistent non-production authorization applies.
- A branch update is known to trigger production deployment, publication, migration, or another external side effect not covered by the persistent non-production authorization.

The built-in persistent authorization is exact: remote `origin` and target `dev`, `develop`, `test`, or `uat`. Another target requires either current-task authorization or a qualifying user-confirmed project or domain policy defined above.
