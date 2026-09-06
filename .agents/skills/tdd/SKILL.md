---
name: tdd
description: Implement behavior test-first with a red-green feedback loop. Use for explicit TDD requests or feature/bug work that needs meaningful behavioral regression coverage. Do not route reversible copy, formatting, or low-impact edits here merely because they change code.
---

# Test-Driven Development

Use red -> green feedback to build one vertical behavior slice at a time.

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
6. Run other project-required checks relevant to the changed surface. Broaden or repeat passing checks only for new changes, failures, or unresolved risks.

## Test Quality

- Expected values must come from a spec, worked example, fixture, or known-good literal, not from recomputing the implementation.
- Avoid tautological tests and snapshots that only freeze incidental structure.
- Prefer behavior tests through public interfaces over mocks of internal calls.
- Keep tests stable across refactors that preserve behavior.

## Harness Duties

- Apply the Harness Capture Gate before documenting a discovered rule; consult `domain-modeling` only for a material terminology or invariant decision.
- If the rule is mechanically checkable, add or update a deterministic test/script/lint/CI check when appropriate.
- For medium or large edits, follow the user's risk-based worktree and documentation workflow before implementation.
