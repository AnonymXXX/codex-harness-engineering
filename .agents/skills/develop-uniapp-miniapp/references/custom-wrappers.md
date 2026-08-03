# Custom Wrappers

## What Belongs In A Wrapper

Create or extend a wrapper when the logic is reused across multiple routes or domains and one of these is true:

- it hides platform APIs
- it centralizes error, loading, or retry behavior
- it coordinates multiple lifecycle hooks
- it standardizes a repeated UI interaction pattern

## Local-First Rule

- If the logic is owned by one route, keep it in that route's `hooks/` directory first.
- Promote route-local logic to `src/hooks` or another shared wrapper only after cross-route reuse or when the pattern is already clearly generic.
- Keep presentational components free of request orchestration, store writes, and platform-API coordination when a hook can own that behavior.

## Common Wrapper Categories

- feedback helper
- request client
- paged list controller
- scroll wrapper
- anchored scroll helper
- media upload helper
- share helper
- realtime event binder
- global modal wrapper
- formatting and error helpers
- permission or environment helpers

## What Stays Local

- one-off field mappings
- single-route lifecycle or interaction orchestration
- single-page derived text
- business-only action grouping
- domain-specific payload assembly used by one route

## Reuse Rules

- Reuse an existing wrapper before adding a new one.
- Extend a wrapper only when the added responsibility fits its current role.
- Prefer a page-local hook over a new global wrapper when the logic still belongs to one route.
- If the new logic would make the wrapper handle two unrelated concerns, keep it separate.

## Naming Rules

- Prefer generic names such as `useFeedback`, `usePagedList`, `AppScroll`, `AppModal`, `useAppModal`, `useAnchoredScroll`, `useUpload`, `useRealtimeEvents`, `requestClient`, `sessionStore`, or `formatErrorMessage`.
- Do not encode brand words, business words, or stylistic themes into new generic abstractions.

## Existing Code Boundary

- Do not rename existing wrappers to satisfy this guide.
- Do not proactively migrate current pages onto a new wrapper unless the user requested that refactor.
