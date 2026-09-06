---
name: diagnosing-bugs
description: Diagnose hard bugs, flakes, regressions, and performance issues through reproduction, minimization, hypothesis, instrumentation, fix, and regression testing. Use when root cause is unclear, behavior is intermittent, a first fix failed, or the user asks to debug/diagnose a problem rather than simply implement known behavior.
---

# Diagnosing Bugs

Do not guess. Build a tight feedback loop, then fix the smallest proven cause.

## Process

1. Reproduce the bug with one command or one clearly described manual path.
2. Minimize the reproduction until unrelated moving parts are removed.
3. Compare expected behavior against docs, tests, specs, and code.
4. Form one hypothesis at a time.
5. Instrument narrowly with logs, assertions, temporary probes, or focused tests.
6. Fix only after evidence supports the cause.
7. Add or update a regression test at the highest practical public seam.
8. Run focused validation and applicable project-required checks. Broaden only when the affected surface or unresolved evidence justifies it.

## Guardrails

- If reproduction is impossible, report what was tried and what evidence is missing.
- Do not perform broad refactors during diagnosis unless the lack of a seam blocks regression coverage; in that case, use `$codebase-design`.
- If the bug reveals a candidate durable invariant, apply the Harness Capture Gate before writing it; use `domain-modeling` when terminology or ownership needs clarification.
- Remove temporary instrumentation before finishing unless it is intentionally retained as useful observability.

## Completion

Report:

- reproduction command or path;
- root cause and evidence;
- fix summary;
- regression test added or why none was possible;
- validation commands run.
