---
name: release-ops
description: Handle release promotion requests that inspect commits on `uat`, find changes missing from `release` or `master`, cherry-pick them in source order, create SemVer tags, and push. Use for prompts about “哪些提交没上 release/master”, “上生产”, “发版”, “推上去”, “发到release”, “cherry-pick 到 release”, feature-based backporting, or release-tag publishing, including inspect-only prompts.
---

# Release Ops

Use this skill for git release promotion tasks that follow a repeatable backport workflow.

## Worker Routing

Follow the shared dispatch, concurrency, safety, and review rules in `~/.codex/docs/workflows/harness-engineering.md`; this section maps only this skill's phases.

- Prefer `luna_worker` with `Route: release-ops/inspect` for inspect-only release evidence: branch/ref/tag inventory, patch-equivalent comparison, candidate commits, blockers, and tag suggestions; it must not execute mutations.
- Keep execution, cherry-picks, tag creation, branch/tag pushes, conflict resolution, and final remote verification with the main agent.

## Defaults

- Default source branch: `uat`
- If default `uat` does not exist, stop and ask the user to specify the source branch.
- Target production branch: prefer `release`, otherwise `master`
- Timezone for relative dates: `Asia/Shanghai`
- Default author name: current repo `git config user.name`; fall back to `assets/defaults.json`
- Author matching: git `author name`
- Author scope: only process the current author by default; include another author only when the user explicitly names that author or asks to process that other author's commits.
- Missing-on-target rule: patch-equivalent, not raw commit hash
- Preflight checks: `git fetch --all --prune --tags` and clean `git status`
- Tag style: lightweight

## Script

Use `scripts/release_ops.py` for deterministic execution.
Resolve script paths relative to this skill directory. The installed path is:

```bash
~/.agents/skills/release-ops/scripts/release_ops.py
```

Do not use the legacy `~/.codex/skills/release-ops/...` path; this skill is installed under `~/.agents/skills`.

Typical flow:

1. Run `inspect` first.
2. Review blockers, warnings, pending commits, target branch, and proposed tag.
3. Run `execute` only when the script reports no blockers.
4. If the only blocker is the pending-count threshold and the user confirms `全部执行`, rerun with `--confirm-all`.
5. Use `--sync-target` with execute mode when the local target branch may be behind `origin/<target>`; it only fast-forwards when there are no local-only target commits.
6. After execute mode finishes, the script restores the branch that was checked out before execution when possible.

Examples:

```bash
python3 ~/.agents/skills/release-ops/scripts/release_ops.py inspect \
  --repo "$PWD" \
  --since 2026-04-14 \
  --until 2026-04-14T23:59:59+08:00
```

```bash
python3 ~/.agents/skills/release-ops/scripts/release_ops.py execute \
  --repo "$PWD" \
  --feature "结算统计页面" \
  --bump auto \
  --sync-target
```

Short natural-language prompts should usually omit the target branch and bump type:

- `帮我查找今天提交但还没有合并到生产分支的提交，cherry-pick过去并推送`
- `帮我查找 Anonym 提交到 uat 的合同筛选功能，但还没上生产分支的，cherry-pick 并推送`

Stable shorthand prompts:

- `今天没上生产的提交，推上去`
- `今天没上生产的提交，发版`
- `合同筛选功能没上生产的提交，发到release`
- `合同筛选功能没上生产的提交，上生产`

Do not rely on bare action words alone. For stability, shorthand execute prompts still need a selector such as:

- a time scope like `今天`, `昨天`, `一周内`
- a feature scope like `合同筛选功能`

## Mode Detection

Interpret the prompt as **execute mode** when it contains action intent such as:

- `cherry-pick`
- `合并到`
- `打 tag`
- `推送`
- `上生产`
- `发版`
- `推上去`
- `发到release`

Otherwise treat it as **inspect-only mode**.

## Commit Selection

Support these selectors:

- author + relative time
- author + absolute time range
- author + feature keyword
- author + feature keyword + time range

If the prompt omits the author, use the current repo `git config user.name`; if unavailable, use the configured default author. Do not include commits by other authors unless the user explicitly names that author or explicitly asks to process that other author's commits.

If the prompt gives a feature keyword but no time range:

1. search the last 1 week,
2. then expand by 1 week at a time,
3. stop after 1 month,
4. report no match if still empty.

Feature matching details live in `references/matching-rules.md`.

## Execution Rules

- If pending commits after filtering are `0`, report no action needed.
- If pending commits are `1-5` in execute mode, execute directly.
- If pending commits are `>5`, stop and offer only:
  - `全部执行`
  - `取消`
- `inspect` always fetches first and analyzes against the latest remote target ref such as `origin/release`.
- In execute mode, use `--sync-target` to fast-forward the local target branch to the remote target before cherry-picking when it is safely behind.
- `--sync-target` must not resolve local-only commits or diverged target branches; stop and report those cases for manual handling.
- Cherry-pick multiple commits in original source-branch chronological order.
- Attempt conflict resolution before stopping.
- The script currently aborts failed cherry-picks and reports the conflict files; if needed, resolve manually after the script stops.
- After execution, switch back to the branch that was active before the run when restoration is possible.

## Tag Rules

- If the user explicitly says `major`, `minor`, or `patch`, follow SemVer exactly.
- If the prompt implies execution but omits the bump type, infer it using `references/matching-rules.md`.
- Only stop for confirmation when bump inference is not confident enough.
- Use the latest SemVer tag reachable from the target branch only.
- If the latest reachable tag is not `vX.Y.Z`, stop and report the problem.
- Before creating the tag, clearly state: current reachable tag -> target tag.

## Risk Stops

Stop and ask before continuing when any of these happen:

- the prompt has only an execute alias such as `上生产` or `发版` but no selector
- default source branch `uat` is absent
- `release` and `master` are both absent
- feature keyword is too vague, such as only `优化`, `修改`, or `调整`
- more than one unrelated feature cluster matches
- related commits from other authors are detected
- bump inference is low confidence
- conflict resolution is not reliable
- pending commits exceed the confirmation threshold

## Output Shape

Inspect-only mode:

- list only `commit sha + subject`
- if other-author related commits exist, call that out separately
- include a coarse bump suggestion

Execute mode:

1. summarize the matched pending commits
2. report the target branch
3. report the tag plan
4. cherry-pick
5. push branch and tag
6. verify remote refs

## Resources

- Deterministic CLI: `scripts/release_ops.py`
- Matching and bump heuristics: `references/matching-rules.md`
- Default config template: `assets/defaults.json`
