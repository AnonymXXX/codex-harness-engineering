---
name: codebase-design
description: Design deep modules, clean interfaces, adapters, and test seams. Use when deciding where a seam goes, improving module shape, reducing shallow pass-through code, making code more testable or AI-navigable, or discussing architecture in terms of interface, depth, locality, and leverage.
---

# Codebase Design

Use a small shared vocabulary to design code that is easier for humans and Codex to change.

## Worker Routing (PAUSED)

子代理强制委派已暂停（用户决定，2026-08-06）。主 agent 默认直接完成本技能范围内的工作；仅当用户明确要求、或并行派发能实质缩短等待且任务边界清晰、可独立验证时才使用子代理。原路由说明已移除，可从仓库 git 历史恢复。

## Vocabulary

- **Module**: anything with an interface and implementation, from a function to a package.
- **Interface**: everything a caller must know: type shape, invariants, ordering, errors, config, and performance expectations.
- **Implementation**: what is hidden behind the interface.
- **Seam**: where behavior can vary without editing the caller.
- **Adapter**: a concrete implementation that satisfies an interface at a seam.
- **Depth**: how much behavior sits behind how little interface.
- **Leverage**: capability gained by callers from a small interface.
- **Locality**: bugs, changes, and verification stay concentrated.

Use these terms consistently. Avoid vague substitutes like "component", "service", "API", or "boundary" when the exact concept is interface, seam, module, or adapter.

## Design Heuristics

- Prefer deep modules: small interface, substantial behavior behind it.
- Use the deletion test: if deleting the module merely moves complexity to callers, it was shallow.
- The interface is the test surface. If tests need to reach past it, reconsider the module shape.
- One adapter means a hypothetical seam; two adapters or a real variation point means a useful seam.
- Accept dependencies instead of creating them internally when it improves testability.
- Return results where practical; avoid making all behavior observable only through side effects.

## Harness Fit

When a design decision becomes durable:

- capture product behavior in product/spec docs;
- capture engineering rules or invariants in engineering-rule docs;
- add executable checks when the rule can be mechanically verified;
- avoid broad refactors unless they directly support the current change or a documented execution plan.

For implementation, hand off to `$tdd` after agreeing the public seam and expected behavior.
