# Scroll View Patterns

Use this file when adding or modifying vertical or horizontal `scroll-view` surfaces, pull-to-refresh logic, load-more logic, or anchored chat-like scrolling.

For complete list-heavy features, also read `feature-slice-delivery.md` so route placement, API/mock flow, list hooks, and empty/error/loading states are planned together.

## Strategy Matrix

- Use a plain `scroll-view` when the surface only needs vertical scrolling and static content sections.
- Use native `refresher-*` when the page needs simple pull-to-refresh with platform-default behavior or only light styling.
- Use a shared custom scroll wrapper such as `AppScroll` when the page needs a custom refresh indicator, coordinated refresh plus load-more, top-detection tolerance, or stronger gesture control.
- Use a tabbed scroll container when the page needs multiple tabs, independent scroll position per tab, pull-to-refresh, load-more, and optional horizontal swipe.
- Use an anchored scroll hook such as `useAnchoredScroll` for chat, threaded comments, or any list that should stay pinned near the newest item.
- Use horizontal `scroll-view` only for chip bars, tab strips, media rows, or other secondary horizontal surfaces, not as the page's primary vertical scroll container.

## Native Refresher Rules

- Prefer native refresher for simple feeds, settings lists, and forms where the default WeChat pull feedback is acceptable.
- When native refresher is chosen, wire `refresher-enabled`, `refresher-triggered`, `@refresherrefresh`, and when reset behavior matters also `@refresherrestore` and `@refresherabort`.
- Use `refresher-default-style` with a platform style when the default indicator is acceptable; use `none` only when the final answer is actually a custom wrapper approach.
- Use `refresher-background` only for light compatibility theming, not as a substitute for a full custom refresh header.
- Pair native refresher with `@scrolltolower` or `lower-threshold` only when load-more is simple and does not need observer-based coordination.

## Custom Refresh Wrapper Rules

- Prefer a shared wrapper when the page needs a custom pull indicator, pull distance control, success or error state display, or stronger control over scroll locking.
- Keep the refresh indicator, pull gesture logic, and `scroll-view` separate even if one component composes them together.
- Keep one `scroll-view` instance alive through refresh; do not swap between two instances with `v-if` or `v-else`.
- During refresh, lock the current scroll position instead of letting inertia continue unchecked.
- Normalize tiny non-zero `scrollTop` values near the top or handle `@scrolltoupper` so a rapid return-to-top does not block the next pull gesture.
- Prefer `IntersectionObserver` for load-more in shared wrappers when the footer trigger node can be observed reliably.

## Vertical Scroll Height Rules

- A `scroll-view` only adapts height correctly when every ancestor in the shrink path allows it.
- Default page skeleton: outer content shell `flex-1 min-h-0 flex flex-col overflow-hidden`, inner scroll slot `flex-1 h-0`, and the `scroll-view` itself `h-full w-full`.
- When the route uses a shared `PageLayout`, keep one primary vertical `scroll-view` inside the content slot and keep fixed bottom actions or shared tabbar UI outside that scroll surface, ideally through the `bottom` slot.
- If the scroll region sits inside multiple nested flex columns, add `min-h-0` to each ancestor that must shrink.
- When the immediate scroll slot is inside a fixed-height flex section, use `h-0` or `flex-1 h-0` on that slot.
- When sticky headers, sticky tabs, or swipe tracks make the flex chain brittle, measure the container height and subtract the fixed-top height instead of nesting deeper.
- Put safe-area bottom padding on the scroll content container, not on the outer layout shell.

## Chat And Anchored Scroll Rules

- Prefer `scroll-into-view` for steady anchored scrolling to the newest item.
- Use `scroll-top` only as a force-scroll fallback when the anchor does not move, the value is ignored, or keyboard or panel animations shift layout after render.
- Track whether the user is near the bottom before auto-scrolling.
- Keep unseen-count or “new messages” state outside the presentational message list.
- Re-run anchor scrolling after layout shifts such as keyboard open, emoji panel toggle, or delayed image load when the user is still near the edge.

## Scrollbar Visibility Rules

- For newly added or user-requested modified `scroll-view` surfaces, default to `show-scrollbar="false"` unless the user explicitly asks to keep scrollbars visible.
- In uni-app mini-program projects that hide scrollbars by default, keep the global scrollbar suppression rule in `App.vue` or the repo's `AppShell`, for example with `scroll-view::-webkit-scrollbar` and `::-webkit-scrollbar`.
- Do not repeat page-local scrollbar pseudo-element hacks when `AppShell` already owns the global scrollbar policy.

## Horizontal Scroll Rules

- Use `scroll-x` for chip bars, tabs, filter strips, and media carousels.
- Hide the scrollbar only when the surface still communicates overflow through layout, gradient fade, or explicit affordances.
- Use `whitespace-nowrap`, `inline-flex`, or `flex` plus `shrink-0` items so horizontal content does not wrap unexpectedly.
- Do not mix the page's primary vertical scroll responsibility into a horizontal strip component.

## Existing Code Boundary

- Reuse an existing shared scroll wrapper, tab container, or anchored-scroll helper before adding a new one.
- Extend an existing stable container when the responsibility still fits its role.
- Do not replace an existing stable scroll implementation unless the user asked for that change.

## Defaults

- Default to a plain `scroll-view` for simple vertical content.
- Default to native refresher for simple pull-to-refresh.
- Default to a custom wrapper for custom refresh visuals or complex refresh plus load-more coordination.
- Default to a measured-height tab container for sticky headers plus tabbed nested scroll surfaces.
- Default to anchored scrolling for chat-like newest-first surfaces.
