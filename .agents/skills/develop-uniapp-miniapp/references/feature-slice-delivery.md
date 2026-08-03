# Feature Slice Delivery

Use this file when the user asks for a complete feature, page family, workflow, or early-stage module instead of a narrow one-file change.

## Delivery Shape

- Start from the user workflow, not from a single route file.
- Define the minimum route set for the workflow: entry page, list/search page, detail page, form/edit page, success/result page, and supporting settings pages only when needed.
- Register every new route in `pages.json`, using the main package for startup and tab pages and subpackages for low-frequency detail or management pages.
- Implement route entries with `PageLayout` or the repo's equivalent page shell.
- Put page-owned visual blocks in the route's `components/` directory and page-owned orchestration in `hooks/`.
- Keep prototype/sample display data in route-local `data.ts` until the task needs real transport or cross-route reuse.
- Add or extend `api` modules only when the feature needs transport-shaped IO.
- Add or extend a store only when state is shared across pages, must survive navigation, or coordinates app-level UI.

## Implementation Passes

1. Inventory existing primitives: page shell, tabbar, scroll/list wrapper, request client, session store, modal/feedback, icon setup, and mock/API layer.
2. Choose package placement and route names before writing components.
3. Sketch data flow: static route-local data, mock service, API module, store, or a mix that matches the repo's current maturity.
4. Build the page shell and navigation handoff first so the feature can be opened.
5. Add route-local components for stable sections such as filters, cards, summary panels, form sections, and action bars.
6. Add hooks for pagination, refresh/load-more, route params, form state, or platform coordination.
7. Wire empty, loading, error, disabled, success, and retry states before final styling.
8. Verify route registration, TypeScript, lint, and platform build or current dev output as the repo expects.

## Route And Package Defaults

- Keep `tabBar` pages, startup pages, login/identity entry, and shared resources in the main package.
- Use one subpackage per low-frequency feature cluster rather than many tiny subpackages.
- Keep list/detail/edit pages for the same management area in one subpackage unless a startup page must stay in the main package.
- Add `preloadRule` only when there is a high-probability next hop from an entry page to a subpackage.

## Data Flow Defaults

- For prototype-led or UI-first work, start with route-local `data.ts` or a local mock service.
- For API-shaped work, place endpoint functions in `api` and keep request mechanics in the shared request client.
- For monorepos with shared contracts, import stable enums and DTOs from the shared package instead of redefining them in pages.
- For feature state used by multiple routes, create a feature store with actions that call `api` modules and expose loading/error states.
- Keep one-off display mapping near the route; promote only reused mappers to shared utilities.

## List And Scroll Defaults

- Use the repo's existing list hook or scroll wrapper first.
- For simple lists, native refresher plus `@scrolltolower` is enough.
- For custom pull visuals or coordinated refresh/load-more, use the shared scroll wrapper template or existing equivalent.
- For tabbed lists with independent tab state and horizontal swipe, use a measured tab-scroll container.
- Always include empty, loading, finished, load-error, and refresh-error handling for user-facing lists.

## Form And Detail Defaults

- Keep form state in the route or route-local hook.
- Split repeated form sections into route-local components with props and emits.
- Use the shared modal/confirm wrapper for simple destructive or submit-confirm flows.
- Put final submit IO in an `api` module and keep payload assembly in the route or feature hook.
- Detail pages should load the primary record first, derive display state with computed values, and keep share handlers close to the page.

## Acceptance Checklist

- All new pages are reachable through declared routes or explicit navigation.
- Shared primitives are reused instead of duplicated.
- No business-specific names from unrelated reference apps are copied into generic abstractions.
- Scroll surfaces have stable height chains and do not put horizontal padding directly on vertical `scroll-view`.
- Visible text is at least `20rpx`.
- Empty/error/loading/finished states are visible and recoverable where applicable.
- Validation commands were run, or the final answer explains why they could not be run.
