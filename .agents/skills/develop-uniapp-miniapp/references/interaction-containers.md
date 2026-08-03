# Interaction Containers

Use this file together with `scroll-view-patterns.md` and `flex-layout-rules.md`.

## Use The Simplest Container First

- Use a plain `scroll-view` when the page only needs vertical scrolling.
- Use native `refresher-*` when refresh is simple and the platform-default visual is acceptable.
- Use a basic or shared list wrapper when the page needs coordinated refresh and load-more.
- Use a tabbed interaction container only when the page truly needs tab-specific scroll state plus gesture coordination.

## Scroll Strategy Escalation

- plain `scroll-view`
- native refresher list
- shared custom scroll wrapper
- tabbed scroll container
- anchored chat scroll

## Tabbed Container Requirements

Use a composed container when all of these are present:

- multiple tabs
- horizontal swipe or manual tab switching
- independent scroll position per tab
- pull-to-refresh
- load-more observer

## Split The Concerns

Keep these concerns separable even if one component composes them:

- direction lock
- pull-refresh controller
- load-more observer
- tab state
- measurement and layout

## Gesture Rules

- Lock horizontal swipe only after a clear direction threshold.
- Let vertical scroll continue when horizontal intent is not confirmed.
- Disable refresh while a horizontal swipe is active.

## Layout Rules

- Prefer measured container height over brittle deep flex chains when a page mixes sticky headers and nested scroll areas.
- Keep fixed-top height and scrollable content height separated.
- Fixed sections should normally use `shrink-0`.
- Ancestors that must let scroll surfaces shrink should normally use `min-h-0`.
- The direct scroll slot often needs `flex-1 h-0`.
- Keep safe-area bottom padding inside the scroll content layer.

## Observer Rules

- Use one observer per active scroll surface or per tab.
- Recreate observers after refresh or after the tab changes if the trigger node is recreated.
- Guard against duplicate load-more triggers while a load is in flight.

## Chat And Anchored Scroll

- Prefer `scroll-into-view` for newest-item anchoring.
- Keep `scroll-top` as a fallback or force-scroll path when anchors alone are not enough.
- Do not treat chat anchoring as the same problem as a standard feed refresh container.

## Existing Code Boundary

- Do not replace an existing stable container unless the user asked for that change.
- If a page already uses a custom container, extend it rather than introducing a parallel one.
