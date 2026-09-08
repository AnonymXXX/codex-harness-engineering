# Automated Git Worktree Workflow

Use this workflow for medium or large file-modifying tasks inside a Git repository.

## When To Use A Worktree

Use a task-specific worktree when isolation provides concrete value: overlapping user changes, concurrent work, a long-running or interruptible task, broad shared behavior, or deployment, data, security, permission, production, or unclear effects. A cohesive Standard Lane change may use the safe current worktree; size, configuration files, or generated artifacts alone do not require another worktree. State the isolation reason briefly before editing.

Do not create a task worktree for Fast Lane work: a clear, cohesive local change in one repository with a safe current worktree and no shared contracts, shared configuration, dependencies, generated artifacts, migrations, deployment, data, permissions, or security-sensitive behavior. It is also acceptable to edit in the current worktree for other clearly small and low-risk changes when existing uncommitted changes are unrelated and will not be touched, or when the user explicitly asks for that.

File count alone does not determine risk: a one-file security change may require isolation, while a cohesive three-file local feature may not. Do not create a worktree solely because the task modifies code; use one when risk, coupling, repository state, or likely interruption justifies isolation.

Always inspect worktree state first and avoid touching unrelated uncommitted changes.

Before editing any path reached through a symbolic link, resolve it with `realpath`, then identify and inspect the real Git repository root, branch, worktree list, and status that own the target. Apply the risk and worktree rules to that real repository, not merely to the directory containing the link.

## Before Editing

Apply the worktree-creation steps below only when isolation is needed under the criteria above. Otherwise inspect the current branch and status, record its starting OID and intended local integration target, and work there. An existing suitable task worktree is reused, not nested.

- If isolation is needed and the current directory is not already a suitable task-specific worktree, create one from the repository's integration branch.
- Determine the integration branch in this order: project `AGENTS.md` or documented project rule, the current branch's upstream integration branch, `origin/HEAD`, then common integration names such as `main`, `master`, or `develop`. If it is still ambiguous, ask the user before continuing.
- Before creating the task worktree, identify existing changes and preserve them in the original worktree. Dirty or overlapping paths do not by themselves block a separate worktree: start from a verified committed base and reconstruct only attributable, authorized task changes there. If required uncommitted dependencies cannot be separated or their inclusion is not authorized, prepare the dependency diff and ask only about that scope.
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
- Run `uv run ~/.agents/skills/harness-engineering/scripts/worktree_bootstrap.py <absolute-worktree-path>` automatically before the first edit.
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
- browser acceptance state (`not-applicable`, `pending`, `passed`, or `waived-by-high-confidence`), the task/thread reference for any explicit user confirmation or explicit push request, and validation/review/target evidence for a high-confidence waiver;
- concrete next step, such as continue, review, commit, merge, clean up, or ask the user.

If you discover an existing dirty or stale task worktree, inspect it read-only and record the status before taking action. Do not automatically delete, prune, reset, merge, or discard a lingering worktree unless the user explicitly asks or the worktree is proven fully merged and clean under the cleanup rules below.

Do not leave the integration or main worktree dirty just to record ledger status. If the current task created a ledger or rule-documentation update that is path-isolated, stage it by explicit path and commit it separately, even when unrelated local changes exist elsewhere in the integration or main worktree. Mark that commit in the working notes as a Harness-created docs-only commit. If the ledger update is not path-isolated or overlaps unrelated user changes, do not write it; include the proposed ledger text in the final response instead.

## After Completing The Task

- Run the relevant validation commands. For UI-affecting work, use non-browser checks only unless the user explicitly requests browser validation or a higher-priority instruction requires it; do not run Playwright, Cypress, mini-program E2E, screenshot regression, or interactive browser acceptance by default.
- If an aggregate command includes browser-driven checks, run separable non-browser tests, lint, typecheck, and build commands instead. Report browser coverage that could not be separated and was skipped.
- If validation passes, automatically commit small low-risk implementation changes with a concise commit message unless the task is exploratory, temporary, explicitly marked no-commit, or the user asks to inspect the diff first.
- For medium or large changes, briefly summarize the diff and validation result before committing, then continue without waiting unless the user asked to inspect the diff first or a stop condition applies.
- Treat validated commit, eligible local auto-merge, separately authorized remote integration, and cleanup as the normal autonomous completion path. Do not end with "ready to merge" or ask the user to repeat a merge request when the applicable gates pass. A UI task qualifying for remote auto-integration records browser acceptance as `waived-by-high-confidence`; an explicit current-task push request records `passed`; a commit-only request remains `pending` and does not itself authorize integration.
- Before committing a medium or large change that was made in the current worktree, explain why skipping a task worktree is still safe, what validation passed, and whether unrelated user changes could be mixed in. Continue without waiting unless a `Stop And Ask` condition applies.
- Keep local-target maintenance separate from remote integration. A divergent local `uat`, `main`, or other integration branch is not evidence that the remote target requires an MR and must not block an otherwise safe remote fast-forward.
- Apply [Local Auto-Merge](#local-auto-merge) independently of remote push authorization. If local state prevents merging, preserve it without blocking an independently safe remote integration.
- Run the relevant validation again after any rebase or integration that changes the tested commit.
- After remote integration, fetch the target again and verify the integrated task commit is its ancestor. Synchronize a safe local target when eligible, then remove the merged task worktree and local task branch unless the user asked to keep them. If the local target moved or contains user changes, skip only local synchronization; remote containment still proves the current task branch is safe to clean up.

## Local Auto-Merge

A request to implement or fix includes committing and merging the isolated, validated task into its identified local integration branch. Do this automatically; no separate "merge it" prompt is needed. This also applies to local `main` or `master` and repositories without a remote. It grants no remote push, PR/MR, deployment, release, or production authorization. Explicit "do not merge", "commit only", "keep the branch for review", project review requirements, and requests to inspect the diff first override this default.

When remote integration is already authorized and eligible, complete its preflight/rebase/push first, then synchronize the local target to the final validated commit under the rules below. Otherwise complete eligible local merging without waiting for remote authorization. Do not rebase against a divergent local target merely to synchronize it after a successful remote integration; preserve it and report the mismatch.

Before merging, require all of the following:

- The intended local target and current-task range are known; task commits contain no unrelated work or unresolved decisions.
- Proportionate project-required checks and static final-diff review pass. Required acceptance or approval is not outstanding. Browser acceptance that was not requested remains `pending` and does not alone block this local operation; never describe it as tested or passed.
- The task worktree is clean. The target worktree is clean and not in active use by another task; never switch its branch, stash user work, or reset it to make integration possible. Inspect target state again immediately before mutation. If active use cannot be ruled out, retain the task result.
- The update preserves existing target history, uses `--ff-only`, and has no unauthorized hook or external side effect.

If the target is already an ancestor of the tested task commit, run `git -C <target-worktree> merge --ff-only <task-branch>`. If the target is not checked out, use a temporary integration worktree for that existing branch. If already working on the intended target, the scoped validated commit completes local integration.

If the target advanced, inspect both ranges. For an unshared task branch with an attributable task base, replay only task commits using `git rebase --onto <local-target> <task-base> <task-branch>`, resolve only conflicts whose result is established by task evidence, rerun affected checks and final-diff review, then retry `--ff-only`. Never rebase a shared task branch or rewrite the target. Stop this operation on ambiguous conflicts or repeated target movement; preserve the task and report the concrete blocker.

Verify `git merge-base --is-ancestor <task-commit> <local-target>` after integration. Report local and remote integration separately. When remote integration is unauthorized, finish with "merged locally; not pushed", rather than requesting permission for an optional push. Retain the task branch/worktree until any already-authorized remote integration finishes; otherwise a clean, inactive current-task worktree and branch may be removed after verified local containment, unless the user asked to keep them. Never delete a branch without verified containment or force-remove a worktree.

## Periodic Stale Cleanup

Do not run the global cleanup scan for Fast Lane work. For Standard or Heavy Lane completion, run `uv run ~/.agents/skills/harness-engineering/scripts/harness_doctor.py cleanup --safe --older-than-days 7` only when no successful global cleanup is known within the preceding 24 hours. When uncertain, skip it and leave cleanup to the next periodic Harness maintenance pass.

Cleanup automatically removes only stale `codex/*` worktrees that are clean, fully merged into their integration branch, unlocked, not ledgered, and unused as any process cwd. Age is the newest of directory creation time, directory modification time, and branch commit time. Dirty, unmerged, detached, non-Codex, unknown, active, locked, and ledgered worktrees are retained. Cleanup failure is reported and leaves uncertain worktrees untouched; it does not retroactively invalidate completed implementation work.

## Commit Convergence Before Publication

Treat the current user requirement and its continuous feedback as one final content commit by default. Small fixes, style adjustments, and review corrections for that same outcome are not separate durable history. Unrelated requirements, independently reversible business changes, and unrelated user work remain separate commits even when they are present in the same worktree.

Before the task branch is first published or an MR/PR is created:

1. Inspect the current-task range with `git log --oneline <task-base>..HEAD` and `git rev-list --count <task-base>..HEAD`.
2. If the range contains multiple commits for the same requirement and the branch is unshared, converge them into one content commit using a safe amend or non-interactive squash/rebase flow. Do not include commits or files outside the current requirement.
3. After any amend, squash, or rebase changes the tested commit, rerun the applicable tests, lint, typecheck or build, plus `git diff --check`, before integration preflight.
4. Publish only the converged result. Local checkpoint commits are allowed for interruption safety, but they must not be published as the final history for one requirement.

If the task branch already exists on a remote, treat it as shared: do not automatically rebase it, amend published commits, or force-push it. When multiple related commits are already shared, enable the platform's MR/PR squash option so the target receives one content commit. If platform squash is unavailable or the source branch itself must be rewritten, stop and obtain separate explicit authorization before using `--force-with-lease`. A platform-required merge commit may remain alongside the single content commit. Never rewrite a target branch that already contains the task solely to clean historical commits.

## Remote Integration

Remote integration uses the latest remote target as its source of truth. It does not require checking out, repairing, or merging through a local target branch.

For UI-affecting work, an explicit current-task push request, including push-only or commit-and-push wording, counts as confirmation that browser acceptance passed. Record the status as `passed` with the task/thread source and continue after project-required validation and integration preflight. Do not ask separately whether acceptance was completed. A commit-only request leaves acceptance `pending`. The push request does not authorize production operations, tags, force pushes, other remotes, or MR/PR creation or merge; their existing authorization rules still apply.

### High-confidence auto-integration

These gates govern remote integration; local completion follows [Local Auto-Merge](#local-auto-merge). Without a push request or browser/user acceptance, automatically integrate UI or non-UI work remotely only when all seven gates pass:

1. Requirements and scope are unambiguous, with no unresolved product or implementation choice.
2. Every applicable test, lint, typecheck, build, and `git diff --check` passes.
3. Static final-diff review finds no issue, and no critical non-browser check was skipped.
4. The task worktree is clean and current-task commits are fully isolated from user changes.
5. The target is exactly `origin/dev`, `origin/develop`, `origin/test`, or `origin/uat`, or an existing non-production target covered by the qualifying user-confirmed policy below; no project rule or current-task instruction prohibits pushing.
6. Preflight returns `DIRECT_FF`, a safely handled `REBASE_THEN_FF`, or `ALREADY_INTEGRATED`.
7. The change has no production, tag, force-push, other-remote, data-migration, permission, security-sensitive, or unauthorized external side effect.

For qualifying UI work, record browser acceptance as `waived-by-high-confidence` and save the automatic-check results, static final-diff review, and target branch as evidence. Then complete validation, commit, preflight, normal non-forced push when needed, remote ancestry verification, applicable post-integration validation, and task worktree/branch cleanup. A failed check, doubtful review, skipped critical check, dirty or unisolated worktree, ineligible or prohibited target, excluded side effect, `STOP`, or `MR_REQUIRED` stops auto-integration and retains the task worktree. `MR_REQUIRED` is report-only unless the user separately authorizes the MR/PR flow.

Normal non-forced updates to `origin/dev`, `origin/develop`, `origin/test`, and `origin/uat` have built-in persistent authorization after project-required validation and preflight pass. This authorization includes known non-production CI and deployment effects triggered by those branch updates.

A user-confirmed canonical project or domain policy may persistently authorize additional non-production targets only when it:

- identifies an explicit repository allowlist and bounded branch names or patterns;
- applies only to existing branches on `origin`, normal non-forced pushes, and known non-production CI or deployment effects;
- requires project-defined validation and the same integration preflight;
- excludes branch names containing `main`, `master`, `release`, `prod`, or `production` as a complete segment separated by the start, end, `-`, `_`, or `/`;
- does not authorize tags, force pushes, MR/PR creation or merge, production effects, or another remote.

A project rule or current-task instruction such as "do not push" overrides every persistent authorization. A project policy may narrow the built-in authorization without meeting the extension requirements above; it may expand authorization only under those requirements.

1. Read project rules before choosing an integration mode. Pass `--integration-mode mr-required` only when the project explicitly requires an MR/PR, review, or platform checks before target updates. A rule that says not to commit directly on the target still permits fast-forwarding commits created on a task branch unless it also forbids direct pushes.
2. Complete the commit-convergence check above, including post-rewrite validation when applicable.
3. Run the read-only preflight from the clean task worktree:

   ```bash
   uv run ~/.agents/skills/harness-engineering/scripts/integration_preflight.py \
     <task-worktree> --task <task-branch> --target <target-branch> \
     --task-base <recorded-target-oid> --remote origin --integration-mode auto
   ```

   Automatic push preflight must include `--task-base`. The command fetches the remote target and returns one of `ALREADY_INTEGRATED`, `DIRECT_FF`, `REBASE_THEN_FF`, `MR_REQUIRED`, or `STOP`. JSON output includes `task_base_oid`, whether baseline checks ran as `baseline_checked`, and any `extra_commits` found in `<remote>/<target>..<task-base>`. It returns `STOP` when the task base is not a task ancestor, contains commits absent from the latest remote target, has unrelated or unsafely rewritten history, or cannot identify the current task range. Action classification never grants push authorization. Use `--format json` for machine-readable output. Use `--no-fetch` only in controlled tests or after an independently verified fetch.
4. Handle the result deterministically:
   - `ALREADY_INTEGRATED`: verify the remote ancestry and continue with validation and cleanup.
   - `DIRECT_FF`: when push is authorized, run a normal non-forced `git push origin <task-branch>:<target-branch>`. This applies to any target branch that project policy and the server permit; branch names alone do not force an MR.
   - `REBASE_THEN_FF`: for an unshared task branch, run `git rebase --onto origin/<target-branch> <task-base> <task-branch>` so only current-task commits are replayed. Rerun validation and preflight before push. Never rebase a shared task branch.
   - `MR_REQUIRED`: pause and report it. Persistent non-production push authorization does not authorize creating an MR/PR; follow the MR flow below only after separate user authorization.
   - `STOP`: report the reason and do not integrate.
5. Classify a failed direct push instead of guessing:
   - On non-fast-forward rejection, fetch and rerun preflight against the new remote target. Revalidate after any resulting rebase. Stop if target movement repeatedly prevents a stable update.
   - On an explicit protected-branch or MR-only rejection, report `MR_REQUIRED` and pause. Enter the MR flow only after separate user authorization.
   - On authentication failure, missing permission, unknown hook rejection, or transport failure, stop and report the exact error. Do not assume an MR will bypass it.
6. After a direct push, fetch the target, verify the integrated task commit is its ancestor, and run the applicable post-integration validation. Fast-forward a clean local target only if it still points to the task base, then remove the merged current-task worktree and branch. Skip unsafe local synchronization without touching user state.

### MR Flow

- An authorization to "push and merge" covers pushing the current task branch, creating its MR/PR, merging it, and deleting the merged current-task source branch. Push-only authorization does not authorize creating or merging an MR.
- Use the project's configured provider workflow. For GitHub platform objects use `github-cli-ops`; for GitLab use the established authenticated CLI or the `ego-browser` Task Space path without bypassing platform policy.
- Wait for required automated checks when they exist. If human approval is required, leave the MR open and report that blocker rather than approving on someone else's behalf.
- For UI-affecting work, an explicit request that includes creating or merging the MR/PR also counts as browser-acceptance confirmation. A push-only request does not authorize MR/PR creation or merge, even though it records browser acceptance as `passed`.
- When the shared task branch contains multiple commits for one requirement, enable the platform's squash option before merge. Do not rewrite or force-push the shared source branch merely to make its intermediate history cleaner.
- When checks pass and no human approval is required, merge automatically using the repository's configured merge method. If the required platform flow only offers a merge commit, the configured merge method counts as project permission when the user already authorized push and merge; report the resulting merge commit.
- Verify the task commit is contained in the remote target after merge, then delete the merged current-task remote branch when the platform has not already done so and complete normal local cleanup.
- Release, publication, deployment, migration, and production-operation workflows retain their own stricter rules. If updating a branch is known to trigger one of those side effects, obtain the corresponding authorization in addition to push and merge authorization.

## Stop And Ask

Stop the affected operation and ask only when necessary input or authorization remains unresolved after safe preparation. Existing authorization continues to apply. Continue independent authorized local work; never bypass `STOP`, `MR_REQUIRED`, protected user state, or external-action boundaries. Ask before the affected operation if:

- The target integration branch is ambiguous.
- Existing changes cannot be attributed or safely isolated without overwriting user work or including unauthorized dependencies. First inspect the diff and try a separate worktree from a verified base; an unrelated dirty file is not a reason to ask.
- The task worktree contains changes of unresolved ownership that cannot be left intact while completing the authorized task.
- Validation remains blocked after reasonable in-scope diagnosis, and the next step needs new scope, authority, or unavailable input. A repairable test failure does not require confirmation; diagnose, fix, and rerun the affected checks before integration.
- A remote High-confidence auto-integration gate is unmet, the remote operation is required for the requested outcome, and no separate current-task authorization covers it. An optional unauthorized push is reported as not performed; it does not block eligible local completion.
- A rebase or merge conflict requires an unresolved product, contract, ownership, or authorization decision. Resolve mechanical conflicts within the authorized task when repository evidence determines the result, preserve both sides' intended behavior, and rerun relevant validation. Never use conflict resolution to discard user changes, rewrite shared history, or bypass `STOP` or `MR_REQUIRED`.
- Remote preflight returns `STOP`, target movement repeatedly prevents a stable update, or the remote target is ambiguous.
- Integration would require force push, reset, rebasing a shared branch, deleting unmerged work, or bypassing required platform approval.
- A remote push is required but neither current-task authorization nor the persistent non-production authorization applies.
- A branch update is known to trigger production deployment, publication, migration, or another external side effect not covered by the persistent non-production authorization.

The built-in persistent authorization is exact: remote `origin` and target `dev`, `develop`, `test`, or `uat`. Another target requires either current-task authorization or a qualifying user-confirmed project or domain policy defined above.
