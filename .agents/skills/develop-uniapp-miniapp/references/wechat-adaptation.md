# WeChat Adaptation

## Navigation And Safe Area

- Use `getMenuButtonBoundingClientRect` when aligning custom navigation with the capsule button.
- Do not render a fake WeChat capsule in page UI just because the prototype shows one; the native system capsule already occupies that role in the mini-program chrome.
- If the design needs right-side alignment near the capsule, measure and offset around the native capsule instead of cloning its border, divider, or icon treatment into the page.
- Respect status-bar height and safe-area insets.
- Prefer existing project helpers for system information when they already exist.
- When switching across tab pages, do not rely on query params with `uni.switchTab`; pass one-shot intent through a store or stable cache key.

## Sharing

- Keep `onShareAppMessage` and `onShareTimeline` at the route entry.
- Use `showShareMenu` only when the flow needs to expose share entry points explicitly.
- If the project supports share landing pages or snapshot flows, keep that behavior in a dedicated helper rather than mixing it into each page.

## Permissions

- Keep WeChat permission descriptions in `manifest.json` or the equivalent uni-app config.
- Request location or other sensitive permissions only from the flows that need them.

## Packaging

- Reuse existing subpackage structure when adding routes.
- Prefer `subPackages` as the default field name when creating or editing config, though `subpackages` is also supported.
- Keep startup pages and `tabBar` pages in the main package.
- Keep each single package within the official `2M` limit and treat the total package size ceiling as `30M`.
- Keep infrequently used feature pages in normal subpackages.
- Use `name` on a subpackage when preload rules or human-readable package references benefit from it.
- Keep each `root` stable and feature-oriented; do not nest one subpackage root inside another.
- Use `preloadRule` only from high-probability entry pages to high-probability next packages.
- Default `preloadRule.network` to `wifi` unless the user explicitly wants broader preload behavior.
- Use independent subpackages only for highly self-contained, startup-sensitive flows.
- Remember that independent subpackages cannot rely on main-package styles or other package files during cold start.

## Platform Boundaries

- Treat WeChat behavior as the default when a platform-specific choice is required.
- Avoid introducing H5-only CSS or browser-only APIs into shared mini-program surfaces.
