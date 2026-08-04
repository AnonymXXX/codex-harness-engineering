---
name: tdd
description: Implement behavior test-first with a red-green feedback loop. Use when building a concrete feature, fixing a bug with known expected behavior, adding regression coverage, or when the user asks for TDD, red-green-refactor, integration tests, public seam tests, or test-driven implementation.
---

# Test-Driven Development

Use red -> green feedback to build one vertical behavior slice at a time.

## Worker Routing

Follow the shared dispatch, concurrency, safety, and review rules in `~/.codex/docs/workflows/harness-engineering.md`; this section maps only this skill's phases.

- Prefer `luna_worker` with `Route: tdd/tests` for independent test inventory, focused test authoring, and test execution that returns red/green evidence.
- Route only a bounded Heavy Lane implementation loop to `terra_worker` with `Route: tdd/implementation` after the main agent fixes the public seam, behavior contract, and acceptance criteria; keep design, coordination, integration, and final validation with the main agent.

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
