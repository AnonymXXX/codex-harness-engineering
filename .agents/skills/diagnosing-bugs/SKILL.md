---
name: diagnosing-bugs
description: Diagnose hard bugs, flakes, regressions, and performance issues through reproduction, minimization, hypothesis, instrumentation, fix, and regression testing. Use when root cause is unclear, behavior is intermittent, a first fix failed, or the user asks to debug/diagnose a problem rather than simply implement known behavior.
---

# Diagnosing Bugs

Do not guess. Build a tight feedback loop, then fix the smallest proven cause.

## Worker Routing

Follow the shared dispatch, concurrency, safety, and review rules in `~/.codex/docs/workflows/harness-engineering.md`; this section maps only this skill's phases.

- Use `deepseek_v4_flash_worker` with `Route: diagnosing-bugs/evidence` for independently bounded reproduction, minimization, evidence gathering, hypothesis checks, and regression-test work; return commands, traces, and test results for main-agent review.
- Route only a bounded fix to `deepseek_v4_flash_worker` with `Route: diagnosing-bugs/fix` after evidence supports the cause; keep diagnosis decisions, scope, integration, and final validation with the main agent.

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
