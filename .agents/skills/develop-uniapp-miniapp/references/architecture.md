# Architecture

## Layering

- `App.vue` acts as the default `AppShell` layer in uni-app projects.
- `pages` or `pages*` hold route-level code, and each route can own `components/`, `hooks/`, and local data modules such as `data.ts` for route-local decomposition.
- `components` hold reusable cross-route UI pieces.
- `hooks` hold reusable cross-route orchestration.
- `stores` hold shared session, unread counts, UI state, or durable client state.
- `api` holds endpoint IO and types close to transport.
- `utils` holds low-level primitives such as request, websocket, formatting, signing, analytics, or permission helpers.

## Prototype-Led Repos

- If a repo includes route-matched local prototypes, HTML mock pages, or other checked-in visual artifacts, treat them as the visual source of truth for those surfaces.
- In prototype-led repos, keep the route entry thin and translate the prototype into route-local `components/`, `hooks/`, and `data.ts` before inventing shared abstractions.
- Keep static display data, placeholder content, and prototype-derived arrays in the owning route folder until the task requires real transport or cross-route reuse.
- Do not infer missing request, session, upload, realtime, or subscription layers as reusable conventions just because a UI-first repo does not contain them.
- When the user asks for a complete module or the repo is an early skeleton, read `feature-slice-delivery.md` and `mature-miniapp-patterns.md` before deciding how much foundation to add in one pass.

## Package Boundaries

- Keep startup pages, `tabBar` pages, and package-shared resources in the main package.
- Keep low-frequency feature routes in a normal subpackage when the repo already uses subpackages or the feature is large enough to justify package separation.
- Keep cross-package shared code in main-package shared layers such as `src/components`, `src/hooks`, `src/stores`, `src/api`, or `src/utils`.
- Do not make one normal subpackage depend directly on another normal subpackage's files.
- Use an independent subpackage only when the route flow is highly self-contained and startup-sensitive.

## Vue Defaults

- Use `Composition API` in newly added Vue SFCs.
- Prefer `<script setup lang="ts">` for newly added Vue SFCs with script logic.
- Keep the route entry thin: route params, lifecycle hooks, share hooks, and page-level orchestration stay there; heavy child UI and route-owned logic move out.
- Prefer props down, emits up, and computed derived state over implicit two-way coupling.

## Placement Rules

- Keep global UI hosts and app lifecycle work in `AppShell`, not in `PageLayout`.
- Keep the shared global modal host in `AppShell`, backed by a shared UI store or modal store.
- Put page-owned child UI in the owning route's `components/` directory before reaching for `src/components`.
- Put route-owned orchestration in the owning route's `hooks/` directory before reaching for `src/hooks`.
- Put route-local static display data or prototype content in route-local modules such as `data.ts` before reaching for `src/stores` or `src/api`.
- Put raw network calls in `api`, not inside pages.
- Put shared session and cross-page state in `stores`.
- Put cross-page orchestration in `hooks`.
- Put generic feedback, scrolling, upload, sharing, or realtime primitives in `utils` or `hooks`, depending on whether they need reactive state.
- Stable generic scroll abstractions may include `AppScroll`, `TabScrollContainer`, `useRefreshPull`, `useLoadMoreObserver`, or `useAnchoredScroll` once they are reused across routes.
- Keep business-specific mapping logic near the page or domain module that owns it.
- When a file must be reused across packages, place it in a main-package shared layer instead of copying it into multiple subpackages.

## Reuse Order

1. Reuse an existing wrapper or helper.
2. Extend an existing wrapper if the change stays coherent.
3. Add a new helper only when the logic is clearly reusable beyond the current file.

## Safe Extension Rules

- Do not rename existing abstractions just to align with this skill.
- Do not move files across layers unless the user asked for a refactor.
- When adding a new abstraction, prefer generic names such as `PageLayout`, `AppScroll`, `requestClient`, `sessionStore`, `useUpload`, or `useRealtimeEvents`.
- Avoid project-specific brand prefixes in new generic abstractions.
- Route-local component or hook names may follow the page feature they serve; once promoted to a shared layer, rename the abstraction generically.
- If a UI-first repo has no `api`, `stores`, or shared transport wrappers, treat that as absence of precedent rather than a signal to invent app-wide infrastructure unless the task actually requires it.

## State Strategy

- Keep persistent auth and profile state in a session store.
- Keep transient UI feedback in a UI store or feedback helper, including shared global modal state when the repo has a dedicated modal layer.
- Keep page-local filters, pagination, modal visibility, and tab state inside the page or the route's `hooks/` unless they are reused across routes.

## Page Structure

- Route entry handles lifecycle, route params, share hooks, and page-level orchestration.
- Route entry should render through the shared `PageLayout` by default.
- `AppShell` handles global lifecycle and global UI; `PageLayout` handles route-level structure.
- Complex child content can move into page-local subcomponents or page-local hooks first.
- Prefer one level of page-local composition before creating a global abstraction.

## Promotion Rules

- Start with the owning route unless the abstraction is already clearly shared.
- Promote a route-local component to `src/components` only when it is reused across routes or has become a stable generic interaction container.
- Promote a route-local hook to `src/hooks` only when it is reused across routes or has become a stable generic orchestration pattern.
- Keep business-only field mapping, payload assembly, and one-off display rules close to the route that owns them.
