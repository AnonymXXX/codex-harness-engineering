---
name: tdd
description: Implement behavior test-first with a red-green feedback loop. Use when building a concrete feature, fixing a bug with known expected behavior, adding regression coverage, or when the user asks for TDD, red-green-refactor, integration tests, public seam tests, or test-driven implementation.
---

# Test-Driven Development

Use red -> green feedback to build one vertical behavior slice at a time.

## Worker Routing (PAUSED)

子代理强制委派已暂停（用户决定，2026-08-06）。主 agent 默认直接完成本技能范围内的工作；仅当用户明确要求、或并行派发能实质缩短等待且任务边界清晰、可独立验证时才使用子代理。原路由说明已移除，可从仓库 git 历史恢复。

## Before Writing Tests

- Explore existing tests, package scripts, and validation commands.
- Read project docs and `AGENTS.md` for testing conventions.
- Identify the public seam under test. Prefer the highest existing seam that observes user-visible behavior.
- Confirm the seam when it is ambiguous or costly to change.
- Do not test private methods, internal collaborators, or implementation details unless the project explicitly treats them as public seams.

## Loop

1. Write one failing test for one behavior.
2. Run the smallest relevant test command and confirm it fails for the expected reason.
3. Implement only enough code to pass.
4. Re-run the focused test.
5. Repeat for the next behavior.
6. Run broader validation at the end.

## Test Quality

- Expected values must come from a spec, worked example, fixture, or known-good literal, not from recomputing the implementation.
- Avoid tautological tests and snapshots that only freeze incidental structure.
- Prefer behavior tests through public interfaces over mocks of internal calls.
- Keep tests stable across refactors that preserve behavior.

## Harness Duties

- If a newly discovered rule is reusable, capture it through `$domain-modeling`.
- If the rule is mechanically checkable, add or update a deterministic test/script/lint/CI check when appropriate.
- For medium or large edits, follow the user's risk-based worktree and documentation workflow before implementation.
