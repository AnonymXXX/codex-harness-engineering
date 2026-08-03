# Page Recipes

For complete modules, page families, or multi-route workflows, read `feature-slice-delivery.md` first and then use the recipes below for each route type.

## New Page Checklist

- Confirm whether the route belongs in the main package, a normal subpackage, or an independent subpackage.
- Keep startup pages and `tabBar` pages in the main package.
- Keep routes from the same low-frequency feature cluster in the same subpackage instead of scattering them across many small packages.
- Wrap every new route page in the shared `PageLayout`.
- Use `Composition API` with `<script setup lang="ts">` for new route SFCs that contain script logic.
- If the repo already contains a route-matched local prototype, HTML mock, or other visual artifact for the surface, translate that artifact before redesigning anything.
- Choose the lightest valid scroll strategy before filling in the page body: plain `scroll-view`, native refresher list, shared custom scroll wrapper, tabbed scroll container, or anchored chat scroll.
- Reuse the project's current page shell and navigation pattern when it already fulfills the `PageLayout` role.
- Reuse the shared global modal wrapper for new confirm or alert flows before adding page-local confirmation state.
- Keep route params parsing at the page entry.
- Put page-specific child UI in the route's `components/` directory.
- Put page-specific orchestration in the route's `hooks/` directory.
- Put page-specific static display data or prototype-derived content in route-local files such as `data.ts`.
- Keep new visible text at `20rpx` or above.

## Split Rules

- Extract a page-local component when a UI block has its own visual responsibility, interaction boundary, or clear props and emits surface.
- Extract a page-local hook when a route-owned concern coordinates lifecycle hooks, local state, or platform APIs.
- Start from `assets/templates/page-with-local-hooks/` when a new route already needs a local page entry, child component, and hook split together.
- When a matching prototype exists, mirror its surface hierarchy first, then extract only the stable visual or interaction blocks; do not turn every prototype fragment into a separate component by default.
- Keep route-local prototype data, sample card arrays, and temporary labels close to the page instead of pushing them into shared stores too early.
- Keep trivial markup, one-off field mapping, and single-use derived text in the page entry until they prove worth extracting.
- Promote route-local code to a shared layer only after cross-route reuse or when the abstraction is already generic and stable.

## Package Placement Rules

- Keep launch-critical pages, authentication entry pages, and `tabBar` pages in the main package.
- Use a normal subpackage for tools, settings areas, activity clusters, low-frequency detail groups, or admin-like features that are not part of the primary startup path.
- Use an independent subpackage only when the route can run without depending on main-package code during startup and the startup-speed gain matters.
- Add package-level preload only when a page has a clear, high-probability next hop into another package.

## Paged List Page

Use this recipe for feeds, message lists, inventory lists, notification lists, and directory pages.

- Put the list surface inside `PageLayout`.
- Keep filter state in the page.
- Put complex filter bars, list cards, and empty or error surfaces in route `components/` when they carry their own interaction or presentation boundary.
- Put route-owned pagination, refresh, and observer coordination in route `hooks/` before creating a shared hook.
- Put transport and pagination params in `api` or a list hook.
- Reuse the project's existing scroll, refresh, and empty-state wrappers when present.
- Keep load-more, refresh, and error states explicit.

## Native Refresher List Page

Use this recipe only when the refresh behavior is simple and the platform-default pull feedback is acceptable.

- Put the page shell inside `PageLayout`.
- Keep the scroll slot as `flex-1 h-0` or another explicit adaptive-height slot.
- Wire `refresher-enabled`, `refresher-triggered`, and `@refresherrefresh`; add `@refresherrestore` or `@refresherabort` when state reset matters.
- Keep native refresher styling light; if the page needs a custom indicator, switch to a shared custom scroll wrapper instead.
- Keep footer load-more logic simple; escalate to an observer-based wrapper when coordination grows beyond one route.

## Custom Refresh List Page

Use this recipe when the page needs a custom pull indicator, coordinated refresh and load-more, or stronger gesture control.

- Prefer an existing shared scroll wrapper before adding a new one.
- Keep one `scroll-view` instance alive through refresh.
- Keep pull indicator UI, pull gesture logic, and load-more logic separable even if one wrapper composes them.
- Put safe-area bottom padding on the scroll content layer, not on the outer page shell.
- Keep empty, loading, finished, and retry states explicit.

## Form Page

Use this recipe for publish, edit, settings, and profile forms.

- Put the form surface inside `PageLayout`.
- Keep form state in the page or a page-local hook.
- Put grouped field sections, sticky action bars, or reusable modal surfaces in route `components/` when they have stable props and emits.
- Use the shared global modal for lightweight confirm or info prompts; keep complex form sheets or custom bodies page-local.
- Put upload in a dedicated upload helper.
- Put final submit in an `api` module.
- Trigger follow-up subscription or share prompts only after success.

## Detail Page

Use this recipe for content detail, order detail, or item detail.

- Put the detail surface inside `PageLayout`.
- Load the primary record first.
- Keep derived display state in computed values.
- Put rich content blocks, action panels, or comment surfaces in route `components/` when they grow beyond simple markup.
- Keep share handlers close to the page entry.
- Only add polling or realtime binding when the detail must stay live.

## Chat Or Realtime Page

- Put the chat page shell inside `PageLayout`.
- Use a dedicated message-management hook.
- Separate message loading, anchored scroll behavior, input panels, and media sending.
- Keep message items, composer panels, and auxiliary drawers in route `components/` unless they are already shared across routes.
- Prefer `scroll-into-view` for stable anchored scrolling and keep `scroll-top` as a force-scroll fallback.
- Track whether the user is near the bottom before auto-scrolling to the newest item.
- Bind realtime handlers on `onShow`.
- Unbind realtime handlers on `onHide` and `onUnload`.

## Horizontal Strip Inside A Page

Use this recipe for tab rows, chip selectors, quick links, and horizontal media strips.

- Keep the horizontal strip secondary to the page's primary vertical scroll surface.
- Use `scroll-x` plus `whitespace-nowrap`, `inline-flex`, or `shrink-0` items so the row does not wrap.
- Hide the scrollbar only when the UI still communicates overflow through spacing, gradient fade, or another affordance.
- Keep text sizes at `20rpx` or above even in compact chips or counters.

## Tabbed Scroll Container Page

Use this recipe only when a page needs all of these together:

- independent tab state
- horizontal swipe
- vertical scrolling
- pull-to-refresh
- load-more

- Keep the page itself inside `PageLayout`, even when the inner surface is a complex tab container.
- Measure the content height when sticky headers, fixed tab bars, or swipe tracks make a pure flex chain brittle.
- Keep tab panels and tab-specific content blocks page-local until another route needs the same generic container.
- Keep refresh state, load-more state, and scroll position independent per tab.
- When only one tab or one scroll area is needed, prefer a simpler container.
