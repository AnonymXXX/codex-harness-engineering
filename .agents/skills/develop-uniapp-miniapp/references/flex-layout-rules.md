# Flex Layout Rules

Use this file when a page or component contains `scroll-view`, sticky headers, bottom action bars, drawers, or any flex layout where a scroll surface must adapt height.

## Core Rules

- Fixed-height or fixed-top sections use `shrink-0`.
- Any ancestor that must let a child scroll surface shrink uses `min-h-0`.
- Any horizontal text column that must ellipsize uses `min-w-0`.
- The immediate slot that owns the vertical scroll surface usually uses `flex-1 h-0`.
- Outer scroll shells usually use `overflow-hidden`.

## Standard Skeletons

### Page Shell

- `PageLayout` owns the app-safe page shell and route-level fixed sections.
- The route content root should usually be `flex-1 min-h-0 flex flex-col overflow-hidden`.

### Fixed Header Plus Scroll Body

- Header, filter bar, or summary strip uses `shrink-0`.
- The direct scroll slot uses `flex-1 h-0`.
- The `scroll-view` itself uses `h-full w-full`.

### Fixed Header Plus Tabs Plus Scroll Body

- Fixed header and tab bar live in a measurable fixed-top region.
- The content body uses measured height when sticky or swipe behavior makes the flex chain fragile.
- Each tab panel owns one `scroll-view` with `h-full`.

### Bottom Action Bar Or Custom Tabbar Plus Scroll Body

- Bottom bar uses `shrink-0`.
- The scroll content keeps bottom spacing in the inner content layer with `pb-safe` or an equivalent token.
- Do not put safe-area padding on the outer container if the bottom bar already owns its own height.

### Modal Or Drawer Scroll Body

- Give the container an explicit `max-height`, viewport-relative height, or measured height.
- Then use `flex flex-col overflow-hidden` plus inner `flex-1 h-0` for the scroll slot.

## When To Use `h-0` Vs `min-h-0`

- Use `min-h-0` on ancestors that only need to allow shrinking.
- Use `h-0` on the immediate flex item that should hand all remaining height to the inner scroll surface.
- Combine them when needed: ancestor chains often need `min-h-0`, while the direct scroll slot often needs `flex-1 h-0`.

## Width Rules

- Use `min-w-0` on flexible text or card bodies inside horizontal flex rows.
- Use `shrink-0` on icons, thumbnails, badges, and pill buttons that must keep their size.
- Avoid accidental wrapping when a `scroll-x` strip really needs `whitespace-nowrap` or `inline-flex`.

## Safe Area And Overflow

- Put `overflow-hidden` on the shell that owns the scroll surface.
- Put safe-area bottom padding on the scroll content layer, not on the whole page shell.
- Keep fixed and scrollable layers separate so the bottom inset does not distort the header or tab height.

## Escalate To Measured Height When

- a sticky header sits above a swipe track or tabbed scroll container
- nested flex columns keep collapsing or stretching unpredictably
- a drawer, sheet, or modal has both fixed and scrollable sections
- the layout mixes top slots, bottom slots, and nested `scroll-view`s in one surface

## Anti-Patterns

- Deep flex chains without `min-h-0`
- Two competing vertical `scroll-view`s in the same region
- Putting `pb-safe` on the outer shell instead of the inner content
- Letting flexible text rows omit `min-w-0`
- Using measured height everywhere when a simple `flex-1 h-0` skeleton already works
