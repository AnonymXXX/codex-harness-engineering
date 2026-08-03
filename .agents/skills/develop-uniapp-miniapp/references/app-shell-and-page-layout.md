# AppShell And PageLayout

## Default Layering

- Treat `App.vue` as the default `AppShell` layer in uni-app projects.
- Keep app launch, foreground/background handling, global styles, and global UI hosts in `AppShell`.
- Keep route-level layout in a shared generic `PageLayout`.

## AppShell Responsibilities

- App lifecycle such as launch, show, hide, reconnect, and bootstrapping.
- Global styles, font registration, and app-wide environment setup.
- App-wide scrollbar policy for mini-program `scroll-view` surfaces, such as global `scroll-view::-webkit-scrollbar` suppression when the project hides scrollbars by default.
- App-wide UI hosts such as toast, loading, modal, or other global overlays.
- By default, keep one shared global modal host in `AppShell`.
- Shared app-level stores or services should connect here, not inside every route page.

## PageLayout Responsibilities

- Status-bar safe-area handling.
- Navigation area and navigation slots.
- Main content slot.
- Bottom slot for tabbar or page-level bottom actions.
- Overlay slot for page-local floating layers.

## PageLayout Interface

- Prefer generic props such as `title`, `showNavbar`, `navMode`, `titleAlign`, `immersive`, `backgroundClass`, `navbarClass`, `contentClass`, and `customBack`.
- Prefer slots named `background`, `nav-left`, `nav-center`, `nav-right`, `bottom`, and `overlay`.
- Keep back behavior generic; do not hardcode business fallback routes into the reusable layout base.
- Keep `PageLayout` free of business tab enums, business route names, and project-specific visual branding.

## Capsule-Aware Navbar

- When the page aligns custom navigation around the WeChat system capsule, measure `statusBarHeight` from `uni.getSystemInfoSync()` and the capsule rect from `getMenuButtonBoundingClientRect`.
- Compute the navigation row height from the capsule height plus the top and bottom gap between the status bar and the capsule.
- Reserve right-side padding from the current window width and the capsule's `left` position so right actions do not slide underneath the system capsule.
- Keep a practical fallback height and right padding when capsule measurement is unavailable.
- Align near the native capsule; do not draw a fake capsule shell, divider, or duplicate icons inside the page UI.

## Tab Page Wrapper

- A thin tab-page wrapper such as `TabPageLayout` is valid when tab pages all share the same route shell plus one shared tabbar.
- Keep the wrapper focused on composing `PageLayout` plus the shared bottom-navigation slot; do not fork the base layout contract for tab pages.
- Keep tab-specific route content in the page entry and page-local components; keep the wrapper generic.

## What Not To Put In PageLayout

- Global `Toast`, `Loading`, or `Modal` hosts.
- Business-specific tabbar implementations.
- Business risk-control overlays or brand-only UI layers.
- Page-local scrollbar pseudo-element hacks when `AppShell` already owns the global scrollbar policy.
- App bootstrap logic, login bootstrap, or websocket bootstrapping.

## Custom Tabbar Integration

- Mount custom tabbar content through the `bottom` slot of `PageLayout`.
- Keep tabbar state and unread badges in stores or feature-layer hooks.
- Do not hardcode tabbar business actions into the generic `PageLayout` base.
- Keep shared Vue tabbar components visually neutral by default; project styles can wrap or extend them without changing the generic layout contract.
- Do not import a business-specific tabbar directly into a generic `PageLayout` for new code.

## Global Modal Integration

- Mount the shared global modal host in `AppShell`.
- Keep route pages on the shared modal hook or wrapper instead of mounting duplicate global hosts.
- A page-local modal component is still valid when the body is feature-specific and not suitable for the shared global modal surface.

## Existing Code Boundary

- For existing repos, reuse or extend the current page shell when it already matches this split.
- Do not proactively migrate old pages to the new split unless the user explicitly asks.
- Apply this structure by default to new routes and user-requested layout changes.
