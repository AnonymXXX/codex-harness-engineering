---
name: diagnosing-bugs
description: Diagnose hard bugs, flakes, regressions, and performance issues through reproduction, minimization, hypothesis, instrumentation, fix, and regression testing. Use when root cause is unclear, behavior is intermittent, a first fix failed, or the user asks to debug/diagnose a problem rather than simply implement known behavior.
---

# Diagnosing Bugs

Do not guess. Build a tight feedback loop, then fix the smallest proven cause.

## Worker Routing (PAUSED)

子代理强制委派已暂停（用户决定，2026-08-06）。主 agent 默认直接完成本技能范围内的工作；仅当用户明确要求、或并行派发能实质缩短等待且任务边界清晰、可独立验证时才使用子代理。原路由说明已移除，可从仓库 git 历史恢复。

## Process

1. Reproduce the bug with one command or one clearly described manual path.
2. Minimize the reproduction until unrelated moving parts are removed.
3. Compare expected behavior against docs, tests, specs, and code.
4. Form one hypothesis at a time.
5. Instrument narrowly with logs, assertions, temporary probes, or focused tests.
6. Fix only after evidence supports the cause.
7. Add or update a regression test at the highest practical public seam.
8. Run focused validation, then broader validation.

## Guardrails

- If reproduction is impossible, report what was tried and what evidence is missing.
- Do not perform broad refactors during diagnosis unless the lack of a seam blocks regression coverage; in that case, use `$codebase-design`.
- If the bug reveals a durable invariant or workflow rule, use `$domain-modeling` to capture it.
- Remove temporary instrumentation before finishing unless it is intentionally retained as useful observability.

## Completion

Report:

- reproduction command or path;
- root cause and evidence;
- fix summary;
- regression test added or why none was possible;
- validation commands run.
