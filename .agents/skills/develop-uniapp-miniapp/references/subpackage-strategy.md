# Subpackage Strategy

Use this file when deciding whether a route belongs in the main package, a normal subpackage, an independent subpackage, or a preload flow.

## Official Baseline

- WeChat recommends using subpackages reasonably to reduce startup download time and improve startup performance.
- A mini-program with subpackages still has one main package.
- The official startup-performance guidance recommends subpackage loading for essentially all mini-programs when used reasonably.
- The main package should hold the default startup page, `tabBar` pages, and shared resources or JS used across packages.
- Normal subpackages can use main-package files and same-package files, but should not directly depend on other normal subpackages.
- `tabBar` pages must stay in the main package.
- Keep a size budget in mind: each single package is capped at `2M`, the overall package total is capped at `30M`, and preload within the same subpackage shares a `2M` preload budget.

## Package Decision Order

1. Is the route part of the startup path, login entry, or `tabBar` navigation?
   - Keep it in the main package.
2. Is the route low-frequency, feature-clustered, and not required for startup?
   - Put it in a normal subpackage.
3. Is the route highly self-contained and extremely startup-sensitive, such as an activity landing page, ad landing page, payment-style flow, or other isolated entry?
   - Consider an independent subpackage.
4. Does the route have a clear, high-probability next hop into another package?
   - Consider `preloadRule` from that entry page.

## Main Package Rules

- Keep startup pages, `tabBar` pages, and startup-critical auth or bootstrap pages in the main package.
- Keep code that must be reused across packages in main-package shared layers such as `src/components`, `src/hooks`, `src/stores`, `src/api`, or `src/utils`.
- Avoid letting the main package absorb every low-frequency feature; otherwise startup size grows too quickly.
- Treat the main package as the strict startup budget, not as the default home for every new route.

## Normal Subpackage Rules

- Group routes by feature domain instead of creating many tiny subpackages.
- Prefer stable feature roots such as `pagesShop`, `pagesActivity`, `pagesTools`, or another existing project convention.
- Use `root` as the package path and keep `pages` relative to that root.
- Add `name` when preload configuration or diagnostics benefit from a package alias.
- Keep low-frequency tools, settings areas, event clusters, and feature-specific detail groups here.
- Watch package size continuously; if one feature package approaches `2M`, split by a stable user-facing feature boundary instead of scattering files arbitrarily.

## Independent Subpackage Rules

- Use independent subpackages only for highly self-contained flows with strong startup-latency requirements.
- Independent subpackages cannot rely on main-package or other-package files during cold start.
- `app.wxss` does not apply during independent cold start.
- `getApp()` may be `undefined` when the mini-program is launched from an independent subpackage page.
- Do not use independent subpackages as a generic answer to package bloat.

## Preload Rules

- Configure package preload with `preloadRule`.
- Use high-probability entry pages as preload triggers.
- Default `network` to `wifi`; use `all` only when the user explicitly wants broader preload behavior.
- Use package `root` or `name` in `preloadRule.packages`; use `__APP__` only when preloading the main package from an independent subpackage flow.
- Do not preload every package indiscriminately; that defeats the startup gain from package separation.
- Remember that preload size is not free: pages in the same subpackage share one `2M` preload budget.

## Reference Boundaries

- A normal subpackage cannot directly import another normal subpackage's JS, templates, or assets.
- Shared code should move to a main-package shared layer instead of being copied or cross-imported from another subpackage.
- If a component or plugin is only used in one subpackage, keep it local instead of registering it globally.

## Defaults

- Default new starter projects to one main package.
- Default to adding subpackages only when the project already uses them, the user explicitly asks for them, or the new feature is clearly large and low-frequency enough to justify package separation.
