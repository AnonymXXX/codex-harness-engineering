---
name: domain-modeling
description: Capture and sharpen a project's domain language, business invariants, reusable engineering rules, and durable decisions. Use when the user defines or changes terminology, business behavior, constraints, data meaning, project rules, architectural decisions, or when another skill needs to maintain project knowledge.
---

# Domain Modeling

Analyze and sharpen project language and invariants without assuming they should be written down. Automatic durable knowledge capture must pass the Capture Gate in `~/.codex/docs/workflows/harness-engineering.md`.

## Explore First

Before proposing or capturing a term/rule, inspect:

- existing `AGENTS.md` files;
- project docs under `docs/`;
- existing glossary, ADR, product spec, engineering rules, or execution plans;
- code that proves or contradicts the stated behavior.

Surface contradictions clearly: "The docs say X, but the code does Y."

## Capture Candidates

Treat these as candidates for the Harness Capture Gate:

- canonical domain terms and overloaded terms;
- business invariants and user-visible rules;
- architecture decisions that are hard to reverse, surprising without context, and chosen after real tradeoffs;
- workflow constraints that prevent likely repeat mistakes;
- mechanically checkable rules that should become tests, scripts, lint rules, or CI checks.

Do not capture one-off preferences, temporary implementation details, speculative plans, obvious local facts, routine validation results, or secrets. Analysis may continue when the gate does not pass, but no file is written.

## Where To Capture

Prefer the project's existing structure. If none exists:

- `docs/product-specs/` for product requirements and user-visible behavior;
- `docs/engineering-rules/` for engineering constraints, invariants, and agent rules;
- `docs/exec-plans/` for larger or interruptible plans;
- `docs/references/` for external research;
- a small glossary file only when shared terminology is actually useful.

Keep `AGENTS.md` short: use it as a map to durable docs, not an encyclopedia.

## Inline Discipline

When a durable decision crystallizes during a task, apply all three Capture Gate conditions before writing it. Product or operational decisions require explicit user confirmation and imminent implementation use. If existing sources conflict, report the conflict and do not choose a canonical answer automatically.

When a rule can be checked mechanically, consider a scoped executable check. Explain why none was added only when it materially affects the task or the user asks.
