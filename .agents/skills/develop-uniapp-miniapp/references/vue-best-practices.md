# Vue Best Practices

## Defaults

- Use `Composition API` for newly added Vue SFCs.
- Prefer `<script setup lang="ts">` for newly added Vue SFCs with script logic.
- Keep route entries thin: route params, lifecycle hooks, share hooks, and page-level orchestration stay in the page entry.
- Keep visible text in newly added UI at `20rpx` or above.

## Component Placement

- Keep page-owned UI in the owning route's `components/` directory first.
- Extract a page-local component when a UI block has a clear visual responsibility, interaction boundary, or stable props and emits surface.
- Promote a component to `src/components` only when it is reused across routes or has become a stable generic container.
- When a component is promoted to a shared layer, rename it generically and remove route-specific or business wording from its public interface.

## Hook Placement

- Keep route-owned orchestration in the owning route's `hooks/` directory first.
- Extract a page-local hook when a concern coordinates lifecycle hooks, local state, or platform APIs for one route.
- Promote a hook to `src/hooks` only when it is reused across routes or has become a stable generic interaction pattern.
- Keep raw transport IO in `api` and shared durable state in `stores`, even when a hook orchestrates them.

## Data And Dependency Boundaries

- Keep props down, emits up, and make inputs and outputs explicit.
- Keep presentational components free of direct request logic, session mutations, or business-only payload assembly.
- Keep derived display state in `computed` values instead of scattered watchers when possible.
- Keep one-off mappings, temporary text assembly, and route-only rules close to the route that owns them.

## Extraction Ladder

1. Keep the code in the route file when the concern is still trivial and page-bound.
2. Move page-owned UI into the route's `components/` directory when the UI surface becomes independently understandable.
3. Move route-owned logic into the route's `hooks/` directory when orchestration becomes heavy.
4. Promote the abstraction to `src/components` or `src/hooks` only after cross-route reuse or when the abstraction is already clearly generic.

## Existing Code Boundary

- Apply these defaults to newly added code and to existing code only when the user explicitly asks to modify it.
- Do not proactively refactor unrelated existing pages, components, or shared hooks just to satisfy this guide.
