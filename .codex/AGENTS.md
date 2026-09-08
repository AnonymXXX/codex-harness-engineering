# Global Agent Rules

## Code Review

For `/review`, `codex review`, and user-requested code reviews, write the final result in Chinese with this structure:

- `总结`: brief result.
- `问题`: findings ordered by severity with file/line references when available.
- `严重级别`: `高`, `中`, or `低` for every finding.
- `修改建议`: concrete fix for every finding.

Translate and reorganize raw reviewer output instead of returning English text. When no issue exists, state `未发现需要修复的问题`.

## Language And Replies

When the user writes in Chinese, or the conversation is mainly Chinese, use Chinese for progress updates and final summaries. Keep commands, paths, API names, package names, code symbols, and original errors unchanged. Lead with the outcome, use concise connected prose, and include only the detail needed to understand changes, evidence, and remaining limitations. Use lists or tables when they improve comparison or sequencing.

## Intent, Scope, And Skill Instructions

Treat action requests as authorization to complete the requested work within its scope. Reuse authorization already established in the session; make routine reversible choices from available context and continue independent work while a necessary question is pending. Prepare a concrete, reviewable result before asking for any additional authorization.

Follow the runtime instruction hierarchy. Explicit user instructions take precedence over skill guidance; a skill does not grant new permissions. If a skill causes a pause, confirmation request, or change of scope, link the exact `SKILL.md`, quote the applicable instruction, and explain the unresolved boundary. Do not infer an approval requirement from an optional recommendation.

## User Input And Choice Prompts

- Whenever the user needs to answer a question, supply missing information, clarify a preference, or make a choice, prefer the runtime's structured input tool (such as `request_user_input`) over asking for a plain-text chat reply. This preference also applies in Default mode when the tool is available and permitted.
- When likely answers can be enumerated, provide concise, mutually exclusive options. When free-form input is needed, use a supported structured free-text input mechanism; do not invent choices merely to fit a tool schema. Ask directly in chat only when the structured tool is unavailable, cannot represent the required input, or is disallowed by higher-priority instructions or its usage rules, including permission or approval requests where prohibited.
- Apply this preference to necessary questions only. Continue already-authorized, unambiguous work without adding confirmation prompts just to trigger the tool.

## Skill Location

Keep user-managed skills under `~/.agents/skills`; reserve `~/.codex/skills` for Codex-managed system skills. After adding, removing, renaming, installing, copying, or migrating one, run `uv run ~/.agents/skills/harness-engineering/scripts/harness_doctor.py index --write` followed by `index --check`.

## Browser And Web Access
联网调研、网页读取、登录态操作、浏览器/CDP 控制和本地页面验证统一使用 `ego-browser`（ego lite）。每个任务使用独立 Task Space，复用其登录态，不抢占用户标签页或切换 macOS 桌面。

在 JumpServer Web 终端中执行命令时，使用页面底部 `Batch commands` 的命令输入框与 `Send` 按钮；不向 xterm Canvas 的隐藏 textarea 注入文本。命令执行后通过终端视口和 CDP 截图核对输出。

不回退、安装或重新启用其他浏览器自动化 Skill。ego lite 不可用或缺少任务所需能力时，按 `ego-browser` 的安装/故障流程处理；仍无法覆盖时明确报告限制并停止对应步骤。任务真正完成后调用 `completeTaskSpace` 并传入 `{ keep: false }`；仅在用户明确要求保留页面或需要在原页面手动操作时使用 `{ keep: true }`，并保留用户原有页面。

## Browser Acceptance

Post-implementation browser acceptance requires an explicit user request or a higher-priority instruction. This does not restrict web research or requested browser operations. Run proportionate non-browser checks and static final-diff review; separate browser-driven checks from aggregate commands and report omitted coverage.

For UI changes, follow [Browser Acceptance](docs/workflows/harness-engineering.md#browser-acceptance) for `自动检查`, `浏览器验收`, `验收步骤`, `通过标准`, `失败判据`, and `集成状态`. An explicit current-task push request records acceptance as `passed`; commit-only leaves it `pending`. A waiver requires every [High-confidence auto-integration](docs/workflows/git-worktree.md#high-confidence-auto-integration) gate. These states never grant additional external-action permissions.

## Human Verification（验证码/人机验证）

在 `ego-browser` 浏览器或网页操作中检测到人机验证（CAPTCHA、滑块验证、点选验证码、reCAPTCHA、登录风控等）时，**立即停止自动化操作**，调用 `handOffTaskSpace` 把当前 Space 交给用户并等待。禁止调用视觉能力尝试自动通过，也不得继续点击、拖拽、刷新或绕过验证。

使用当前运行时可用的用户输入机制说明验证码位置（页面/网址/当前步骤）并等待；优先使用运行时允许且能表达所需输入的结构化工具，否则直接询问。选项至少包含 `已验证`（继续）、`未处理`（跳过或结束当前步骤）和 `取消任务`（终止任务）。

等待用户选择后再继续；用户处理期间不得重复操作页面或重新触发验证码。仅在用户明确选择继续后调用 `takeOverTaskSpace` 取回控制。

## DESIGN.md And UI Consistency

For UI, frontend, styling, or visual-design work, read project-root `DESIGN.md` first when present. Otherwise infer the baseline from existing pages, components, and styles; do not invent a new visual language unless requested. When asked to create `DESIGN.md`, adapt `~/.codex/templates/DESIGN.md` to the existing UI first. Prefer established component conventions over a conflicting `DESIGN.md` and report the conflict.

## Implementation And Risk

- Choose the simplest complete implementation. Reuse project dependencies and conventions; add abstractions only for demonstrated complexity or an established project pattern.
- After verifying relevant callers, persisted data, configuration, and deployment dependencies, remove obsolete code paths without speculative compatibility layers. If evidence is incomplete, verify the dependencies first. A bounded interim solution must state its risk and removal condition.
- Classify risk before editing. Use the `harness-engineering` skill's Fast Lane for small isolated work; read [Harness Engineering](docs/workflows/harness-engineering.md) for broader work and [Git Worktree Workflow](docs/workflows/git-worktree.md) for medium/large Git changes. File count is a signal, not a threshold.
- Before medium/large edits, state whether a task worktree is used. For an applicable exception, explain isolation and validation before committing. Preserve unrelated user changes.
- Run required checks appropriate to the changed surface. Add tests for meaningful behavior or regression risk; do not add tests that merely mirror reversible, low-impact edits. After checks pass, broaden or repeat them only for new changes, failures, or unresolved concerns.

## Destructive Operations

- Prefer `/usr/bin/trash` over permanent local deletion.
- Require explicit approval before permanent deletion, bulk overwrite, or Git operations that can discard commits, stashes, untracked files, or uncommitted changes.
- Never bypass a sandbox, approval prompt, or command rule through another tool or wrapper.
- Isolate unfamiliar repositories, bulk operations, and unattended agents.

## Git Authorization And History

Use [Git Worktree Workflow](docs/workflows/git-worktree.md) for task isolation, commit convergence, preflight, integration, and cleanup. One requirement and its continuous feedback should contribute one final content commit; keep unrelated work separate. Never automatically rewrite shared history or an integrated target.

Normal non-forced pushes to `origin/dev`, `origin/develop`, `origin/test`, and `origin/uat`, including known non-production CI/deployment effects, have persistent authorization after required validation and preflight. Extensions require the workflow's user-confirmed repository allowlist and bounded existing non-production targets on `origin`. A project or current-task prohibition overrides persistent authorization. Other remotes, production targets/effects, tags, force pushes, and MR/PR creation or merge require explicit authorization.

Validated commits and [Local Auto-Merge](docs/workflows/git-worktree.md#local-auto-merge) are default completion steps; do not wait for another merge prompt. Local `main/master` merges do not grant remote push permission. Complete separately authorized remote integration automatically. `STOP` and `MR_REQUIRED` block the affected integration operation; retain the worktree and report the reason. Stale cleanup follows the workflow's periodic cadence and clean/merged/inactive checks, not every task.

## Subagent Delegation

主 agent 默认直接完成工作，强制委派保持暂停。仅当运行时允许，且用户明确要求，或独立、边界清晰、可验证的并行任务能实质缩短等待时使用子代理。不恢复旧 Worker 协议或固定派发配额。

## Vision Delegation

For image tasks, use the current runtime's native image input when available. If the active model cannot inspect images and a configured vision-capable agent is available, delegate the image paths and use its structured description; otherwise ask the user to provide an accessible file or switch to a vision-capable runtime. Do not scrape runtime databases or assume a model, storage schema, or agent name.

## Python Environment

Use `uv run` or the project's `.venv/bin/python` / `venv/bin/python`; do not assume bare `python` or `python3` has project packages. Discover interpreters with `uv python list --only-installed` and install with `uv python install <version>`. Keep machine version inventories out of instructions.

## Documentation And Harness Health

[Harness Engineering](docs/workflows/harness-engineering.md) owns automatic durable-knowledge capture and its Capture Gate; explicitly requested documentation work is already in scope. Use [Document Gardening](docs/workflows/document-gardening.md) when editing durable rules. Preserve business invariants and authorization boundaries; do not write speculative decisions or secrets as project truth.

After Harness skill, workflow, template, or worktree-policy changes, run `uv run ~/.agents/skills/harness-engineering/scripts/harness_doctor.py doctor` (read-only). Skill lifecycle changes also require the index commands under Skill Location.

## Facts And Queries

When the user asks about facts, data, status, rules, policies, prices, product information, or similar, do not answer from memory, training data, or speculation.

- Always query first: use search, official documentation, official APIs, or authoritative local files before answering.
- Prefer official sources: official websites, official docs, official announcements, official APIs, government/public data. Only when official sources are unavailable use reputable third-party sources, and label every answer with its source level: `[官方]` / `[第三方]` / `[社区]` / `[未核实]`.
- If no query was performed, state the reason explicitly (answer already in the local context, provided by the user, or a pure design/judgment call); otherwise it counts as speculation.
- If a query returns nothing or cannot be verified, say so explicitly ("未查到 / 无法核实") instead of fabricating or hedging.
- Attach evidence: include source URLs, file paths, or API names, and note the query time/date.
- Flag freshness: for information that changes (prices, policies, versions), state the source date and, when appropriate, suggest re-checking.
- Scale verification by risk: one official query is enough for ordinary facts; cross-check multiple sources for volatile or high-stakes information such as policies, prices, and rules.
- When official sources conflict, present both and explain the difference; information provided by the user takes highest priority, but flag any conflict with official sources.
