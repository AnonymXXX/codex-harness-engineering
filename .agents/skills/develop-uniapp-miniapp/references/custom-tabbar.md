# Custom Tabbar

When a feature slice needs bottom navigation plus page-shell changes, also read `mature-miniapp-patterns.md` so route source of truth, tabbar state, and page layout are planned together.

## Choose The Mode First

- Distinguish among three patterns before giving implementation advice:
  - native `pages.json` `tabBar`
  - WeChat official `custom-tab-bar/`
  - shared Vue page-shell tabbar mounted through `PageLayout` or another layout base
- Reuse the current pattern unless the user explicitly asks for a migration.
- If a repo only has `pages.json` `tabBar` and does not have `custom-tab-bar/` or a shared bottom-navigation component, treat it as native `tabBar` mode, not as a custom tabbar implementation.
- Treat `pages.json` `tabBar.custom: true` plus a shared Vue bottom-navigation component as a valid custom tabbar mode, even when there is no `custom-tab-bar/` directory.

## Reuse The Existing Pattern First

- If the repo already has a shared page shell plus a bottom navigation component, extend that path.
- If the repo already uses an official `custom-tab-bar/` directory, keep using it.
- Do not introduce both patterns in the same repo unless the user explicitly asks for that migration.
- If the repo already uses Tailwind/Iconify class icons in Vue UI, prefer the shared Vue tabbar path for new custom tabbar work.

## Native TabBar Fit And Limits

- Use native `pages.json` `tabBar` for simple, mostly static bottom navigation.
- Native `tabBar` is a poor fit for rounded floating shells, glassmorphism, raised center actions, dynamic height, class-based icon rendering, or complex badge and animation behavior.
- If the design needs those behaviors and the repo can use Vue UI, prefer the shared Vue tabbar path.
- Use official `custom-tab-bar/` only when the repo already uses it, the user explicitly asks for it, or native mini-program lifecycle integration is more important than Vue component reuse.
- If native `tabBar` is chosen, complete the native config instead of half-implementing a custom design around it.

## Visual Shape Is A Variant

- Do not assume every custom tabbar is a floating or glass-style control.
- If the user provides a UI image, Figma, HTML prototype, or repo-local prototype for the tabbar, follow that visual as the source of truth.
- Only when no UI or established project pattern exists should generic templates default to a standard bottom-navigation shape.
- Treat floating capsules, raised center buttons, split panels, and other visual forms as styling variants.
- Keep generic component names neutral, such as `AppTabbar`, `BaseTabbar`, or `BottomNavigation`.
- When no UI exists and a new tabbar style must be chosen, derive a look that matches the current page design; for design-led fallback work, use the `frontend-design` skill guidance instead of inventing a random generic shape.
- Default active states to color, icon, label, background, border, or shadow changes rather than positional displacement.
- Do not add `translateY`, vertical lift, or similar active-state movement to tabbar items unless the user explicitly asks for that interaction.

## Source Of Truth

- Keep tab routes in `pages.json` `tabBar.list`.
- Mirror those routes through a typed config module only when a custom tabbar component needs icons, badges, labels, or feature flags.
- Only call `uni.switchTab` for routes that are declared as tab pages.
- Keep non-tab actions as explicit action items and handle them through emitted events instead of `uni.switchTab`.
- If a center item is also declared in `pages.json` `tabBar.list`, treat it as a normal tab route with special styling rather than an action.

## State And Cross-Tab Handoff

- Keep unread counts, red dots, and profile-completion badges in a store.
- Derive the active tab from the current route or from a page-shell prop instead of duplicating active state in every page when using a custom tabbar.
- Because `uni.switchTab` does not support query params, pass one-shot cross-tab intent through a store or stable cache key.
- Clear one-shot handoff state after the target page consumes it.

## Layout And Safe Area

- Respect bottom safe-area insets.
- Mount a custom tabbar in one shared place instead of duplicating it inside every tab page.
- Keep label text at `20rpx` or above.
- Keep tap targets comfortable with padding or fixed hit areas.
- Add bottom padding to page content when a custom tabbar overlays content.

## Center Actions And Special Buttons

- Treat a center button or floating action button as optional.
- Emit an action event from the reusable tabbar base and let the page shell or feature layer decide the business behavior.
- Do not hardcode project-specific feature flows into the generic base component.

## Icon, Color, And Badge Rules

- In native `tabBar` mode, use local `iconPath` and `selectedIconPath` assets for each tab item.
- In shared Vue tabbar mode, reuse the repo's existing Tailwind/Iconify classes and font tokens.
- In official `custom-tab-bar/` mode, verify the chosen icon and class pipeline works in native mini-program files before assuming Vue class behavior applies.
- If the repo's visible icon system is mainly Tailwind/Iconify class icons, do not assume native `tabBar` can reproduce that visual system without dedicated image assets.
- Keep active and inactive colors theme-driven.
- Keep badge formatting centralized, for example capping counts at `99+`.
- Keep icon names presentation-focused rather than business-focused.

## Page Shell Integration

- If the repo already has a shared `PageLayout`, mount a shared custom tabbar through its `bottom` slot.
- If the repo already uses a thin tab-page wrapper such as `TabPageLayout` over `PageLayout`, extend that wrapper instead of mounting the shared tabbar separately in every tab route.
- If the repo already has a shared page shell or layout component, extend that path rather than introducing a parallel layout layer.
- In native `tabBar` mode, do not render a duplicate bottom navigation component inside page layouts.
- In official `custom-tab-bar/` mode, keep the tabbar in `custom-tab-bar/` instead of re-creating it in each page.
- In shared Vue tabbar mode, keep `pages.json` `tabBar.custom: true` aligned with the shared component so the native tabbar is hidden while tab routes remain declared.
- Show the tabbar only on tab pages or when the page shell explicitly enables it.
- Avoid wrapping non-tab detail pages with duplicate tabbar instances.

## WeChat-Specific Notes

- `uni.switchTab` changes navigation stack behavior differently from `navigateTo`; keep return-flow logic in page or route orchestration.
- If the project uses official `custom-tab-bar/`, make sure selected state is synchronized whenever the visible tab page changes.
- If the project hides the native tabbar and renders a shared replacement, keep route declarations and replacement UI aligned.

## Diagnostic Checklist

- If a repo only defines `pages.json` `tabBar.list`, has no `custom-tab-bar/`, and has no shared bottom-navigation component, diagnose it as native `tabBar` mode.
- If native `tabBar` items only define text and colors but no icon assets, diagnose the configuration as incomplete rather than calling it a finished custom tabbar.
- If the page UI uses class-based icons but the bottom navigation is still native `tabBar`, expect the tabbar visuals to diverge unless dedicated image assets are added.
- If `pages.json` has `tabBar.custom: true` and the visible tabbar is a shared Vue component, diagnose it as shared Vue custom tabbar mode.
- If `pages.json` leaves the native tabbar visible and a page shell also renders a bottom navigation component, diagnose it as a duplicate-rendering mixed pattern and remove or hide one path.

## Existing Code Boundary

- Do not replace an existing stable bottom-navigation implementation unless the user asks for that change.
- Do not migrate business-specific labels, icon choices, or center-action behavior into generic skill conventions.
