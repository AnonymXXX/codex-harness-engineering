---
name: codebase-design
description: Design deep modules, clean interfaces, adapters, and test seams. Use when deciding where a seam goes, improving module shape, reducing shallow pass-through code, making code more testable or AI-navigable, or discussing architecture in terms of interface, depth, locality, and leverage.
---

# Codebase Design

Use a small shared vocabulary to design code that is easier for humans and Codex to change.

## Vocabulary

- **Module**: anything with an interface and implementation, from a function to a package.
- **Interface**: everything a caller must know: type shape, invariants, ordering, errors, config, and performance expectations.
- **Implementation**: what is hidden behind the interface.
- **Seam**: where behavior can vary without editing the caller.
- **Adapter**: a concrete implementation that satisfies an interface at a seam.
- **Depth**: how much behavior sits behind how little interface.
- **Leverage**: capability gained by callers from a small interface.
- **Locality**: bugs, changes, and verification stay concentrated.

Use precise terms when they clarify the design; preserve the project's established domain vocabulary and explain unfamiliar terms only when needed.

## Design Heuristics

- Prefer deep modules: small interface, substantial behavior behind it.
- Use the deletion test: if deleting the module merely moves complexity to callers, it was shallow.
- The interface is the test surface. If tests need to reach past it, reconsider the module shape.
- One adapter means a hypothetical seam; two adapters or a real variation point means a useful seam.
- Accept dependencies instead of creating them internally when it improves testability.
- Return results where practical; avoid making all behavior observable only through side effects.

## Harness Fit

When a design decision passes the Harness Capture Gate:

- capture product behavior in product/spec docs;
- capture engineering rules or invariants in engineering-rule docs;
- add executable checks when the rule can be mechanically verified;
- avoid broad refactors unless they directly support the current change or a documented execution plan.

Use `tdd` when test-first work is requested or meaningful behavioral regression coverage is needed; a design discussion alone does not require an implementation handoff.
