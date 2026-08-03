# Decoupling Rules

## Never Generalize These Directly

- brand prefixes
- stylistic theme names
- product-domain nouns
- current backend header names
- current signing field names
- current event names
- current template ids

## What To Extract Instead

- page-local components
- page-local hooks
- page shell
- request pipeline
- session store
- paged list controller
- upload helper
- share helper
- realtime manager
- subscription helper
- tabbed interaction container

## Extraction Rule

When current project code contains reusable behavior plus business content, extract only the reusable behavior and rename it generically.

## Promotion Rule

- Start with a page-local component or page-local hook when the behavior is still owned by one route.
- Promote it to a shared layer only after reuse crosses routes and the abstraction can keep a generic name.
- Do not turn one route's business wording, payload shape, or visual theme into a global convention.

## Existing Code Boundary

- Do not rename existing branded or business-specific code unless the user asked for a refactor.
- New abstractions must be generic.
- Existing abstractions may stay as they are if the task only requires extending them locally.
