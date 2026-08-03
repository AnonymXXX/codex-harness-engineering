# Mature Miniapp Patterns

Use this file when a confirmed uni-app project needs stronger frontend foundation, or when translating lessons from a mature mini-program into generic target-project code.

## Extraction Rule

- Extract patterns, not names.
- Keep the target repo's business nouns, visual language, route names, icons, color tokens, and component prefixes.
- Do not copy a mature reference app's brand style, tab labels, center actions, API headers, signing rules, ban logic, or local paths unless the target repo explicitly has the same requirements.
- Prefer generic names for new shared primitives: `PageLayout`, `AppTabbar`, `AppScroll`, `usePagedList`, `requestClient`, `sessionStore`, `uiStore`.

## Foundation Inventory

Before adding pages at scale, check for:

- app shell: `App.vue` lifecycle, global styles, modal/toast/loading hosts, scrollbar policy
- page shell: `PageLayout` or equivalent navbar/content/bottom/overlay slots
- bottom navigation: native tabbar, shared Vue tabbar, or official custom tabbar
- scroll/list: native refresher, shared scroll wrapper, load-more observer, tab-scroll container
- feedback: one modal/toast/loading path usable from pages and non-component files
- transport: one request client, one session/auth store, endpoint modules in `api`
- shared state: stores for session, unread/badge counts, cross-route handoff, and feature state
- assets and icons: existing Tailwind/Iconify or local asset pipeline

Add missing primitives only when the requested feature would otherwise duplicate them.

## Page Shell Pattern

- Keep `App.vue` as app-level shell and global host.
- Keep route layout in `PageLayout`: safe area, custom navbar, content slot, bottom slot, overlay slot.
- Route pages should compose `PageLayout` and pass page-specific title, nav mode, background, and bottom-slot content.
- A thin tab-page wrapper is valid when all tab pages share `PageLayout` plus one app tabbar.
- Do not import business-specific tabbar, risk overlays, or feature stores into generic `PageLayout`.

## Bottom Navigation Pattern

- Keep `pages.json` as the route source of truth.
- Use shared Vue tabbar when the repo wants Tailwind/Iconify UI or richer custom layout.
- Use official `custom-tab-bar/` only for existing native custom-tabbar repos, explicit user requests, or lifecycle-specific native tabbar needs.
- Keep tab item config typed and centralized when a Vue tabbar is used.
- Store unread counts, red dots, and cross-tab handoff in a store, not inside each tab page.
- Treat raised center buttons, dock shapes, capsules, and floating bars as style variants, not architecture names.

## Scroll And List Pattern

- Use one primary vertical scroll surface per page region.
- Use `AppScroll` or the repo equivalent for custom pull indicators, coordinated refresh plus load-more, and footer observer behavior.
- Use a tab-scroll container only when independent tab state, horizontal swipe, vertical scroll, refresh, and load-more are all needed.
- Keep list state in a route-local hook or generic `usePagedList`: `items`, `loading`, `refreshing`, `finished`, `refreshError`, `loadMoreError`, `refresh`, `loadMore`, `retryLoadMore`, `reset`.
- Keep loading minimum-duration or flicker control in the hook or feedback store, not repeated in every page.
- Reset observer or load-more triggers after load completion and when returning to a page if the platform requires it.

## Feedback Pattern

- Keep one app-level path for toast, loading, and modal state.
- Expose a component hook for page code and a safe static wrapper for non-component files such as request clients.
- If loading is visible, queue toast/modal display until loading hides to avoid overlapped feedback.
- Keep modal promises simple for confirm/alert flows; complex forms stay page-local.

## Transport Pattern

- Keep endpoint functions in `api` modules with typed params and responses.
- Keep the request pipeline in one client: base URL, auth header injection, explicit loading, error normalization, and 401 retry.
- Keep optional security additions configurable: handshake, signed headers, client IDs, debug headers, banned-user handling.
- Do not bake a reference app's protocol into a generic request template.
- For mock-first work, mirror the eventual endpoint shape so switching to real API does not rewrite pages.

## Store Pattern

- Session store owns token, user profile, login/logout, silent login, and storage persistence.
- UI store owns global toast/loading/modal and cross-route temporary preview handoff when needed.
- Feature stores own state reused by multiple routes, such as badges, unread counts, cached filter options, or multi-page drafts.
- Page-only filters, pagination, modals, and form state stay route-local.

## Prototype Translation Pattern

- First identify the prototype's shell: navbar, tabbar, primary scroll region, fixed action areas, overlays.
- Translate visible hierarchy into route-local components before inventing shared abstractions.
- Move repeated cards, section headers, filters, and action bars into route-local components.
- Keep temporary arrays and sample text in local `data.ts`.
- Use the target repo's design tokens and icon setup; do not import a reference app's one-off visual theme.

## Completion Signals

- A new feature can be opened from navigation and exercised without console/runtime route errors.
- The feature uses one coherent shell, feedback path, and scroll/list strategy.
- Domain data has a clear owner: local data, mock service, API module, or store.
- The implementation does not contain unrelated reference-project naming or hardcoded local paths.
