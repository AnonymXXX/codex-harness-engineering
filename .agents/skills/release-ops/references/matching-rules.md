# Matching Rules

Use these rules to turn loose prompt language into a stable commit set.

## Execute Aliases

Treat these phrases as execute intent aliases:

- `上生产`
- `发版`
- `推上去`
- `发到release`

These aliases are valid only when the prompt also contains a selector.

Valid selectors include:

- relative time, such as `今天`, `昨天`, `一周内`
- explicit time range
- feature keyword

If an alias appears without a selector, stop and ask for the missing scope instead of guessing.

## Relative Time Parsing

- Parse relative dates in `Asia/Shanghai`.
- `昨天`: previous calendar day in `Asia/Shanghai`.
- `一周内`: current time minus `7 x 24h`.
- For feature-only queries without a time range, expand windows in this order:
  - `1 week`
  - `2 weeks`
  - `3 weeks`
  - `4 weeks`

## Missing-On-Target Rule

Treat “没有合并到 release/master” as:

- no patch-equivalent commit exists on the target branch
- prefer `git cherry` semantics over raw sha comparison

Do not require merge commits because the normal promotion path is cherry-pick.

## Feature Matching Order

1. Commit subject and body keyword match
2. Diff-content keyword match
3. File-path overlap clustering

Default keyword behavior:

- case-insensitive
- phrase contains first
- token overlap second
- no regex by default

## High-Risk Keywords

Treat these as too vague when used alone and stop for confirmation:

- `优化`
- `修改`
- `调整`

If the prompt contains one of these plus a stronger domain term, continue with normal matching.

## Other-Author Handling

Default behavior:

- process only the current repo `git config user.name`
- if unavailable, use `assets/defaults.json`
- include another author's commits only when the user explicitly names that author or explicitly asks for that other author's commits

Primary scan:

- same source branch
- selected author only
- same requested time window if present

Risk scan:

- same source branch
- same time window
- other authors
- only for warning and confirmation

Do not automatically cherry-pick other-author commits during the default current-author flow.

## File Clustering

Use file-path overlap to recover multi-commit features that do not repeat the same keyword in every commit.

Prefer the cluster when:

- matched commits touch the same directory or file group
- commit subjects are adjacent in time or clearly part of the same module work

If multiple unrelated clusters remain after clustering, stop and ask.

## Bump Inference

If the prompt does not explicitly say `major`, `minor`, or `patch`, infer using these rules.

### `major`

Use only for clear breaking changes, such as:

- incompatible route, API, or permission changes
- explicit removal of old behavior
- `breaking`, `不兼容`, `移除旧逻辑`, or equivalent strong signals

### `minor`

Use for additive product work, such as:

- new page, module, menu, export, button, workflow step, or feature
- strong `feat`, `新增`, `增加`, `支持` signals

### `patch`

Use for narrow fixes or adjustments, such as:

- bug fixes
- display fixes
- null guards
- copy or style adjustments
- clear `fix` or `修复` signals

### Precedence

- If a batch contains both fix-like and feature-like commits, infer `minor`.
- If message and diff disagree, trust the diff.
- If any commit clearly requires a higher bump, the batch inherits that higher bump.
- If still unclear after these checks, stop and ask.
