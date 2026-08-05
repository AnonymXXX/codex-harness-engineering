---
name: develop-uniapp-miniapp
description: Build, scaffold, and extend confirmed uni-app/Vue WeChat mini-program projects with a Tailwind-first, local-first frontend workflow. Use for small page changes, full page-family/feature-slice delivery, frontend foundation setup, prototype-to-miniapp implementation, custom tabbar, scroll/list, request/session, modal, store, and subpackage work in repos that are already uni-app or when the user explicitly asks to create or migrate to uni-app. Do not use for native WeChat mini-program repos that primarily use `app.json`, `app.js`, `Page()`, `.wxml`, `.wxss`, `@vant/weapp`, or native `custom-tab-bar` without uni-app markers. Confirm uni-app signals first, then reuse project conventions; when the user asks for a complete feature or the repo is an early skeleton, deliver a coherent frontend slice instead of over-narrowing to one file.
---

# Develop Uniapp Miniapp

Use this skill to deliver uni-app mini-program frontend work, from narrow fixes to complete page-family feature slices, without rewriting unrelated existing code.

Do not use this skill for a native WeChat mini-program repo unless the task is explicitly to migrate that repo to uni-app.

## Worker Routing

Follow the shared dispatch, concurrency, safety, and review rules in `~/.codex/docs/workflows/harness-engineering.md`; this section maps only this skill's capability modes.

- Use `deepseek_v4_flash_worker` with `Route: develop-uniapp-miniapp/small-change` for small isolated changes and focused validation with disjoint ownership.
- Route bounded implementation of complex feature slices or frontend foundations to `deepseek_v4_flash_worker` with `Route: develop-uniapp-miniapp/complex-implementation`; keep mode selection, architecture, UX decisions, integration, and final validation with the main agent.

## Workflow

1. Confirm the repo is a uni-app mini-program project, or that the user explicitly asked to create or migrate one.
2. If the directory is empty or near-empty and the user asked to create a uni-app WeChat mini-program project, scaffold from `references/project-bootstrap.md`.
3. Check whether the root is a Git repository. If it is not, run `git init`.
4. Check whether a root `AGENTS.md` exists. If the repo is confirmed as uni-app and the file is missing, create it using `references/activation-and-agents.md`.
5. If the repo includes a matching local prototype, HTML mock, Figma handoff, or other visual artifact for the surface, treat that artifact as the visual source of truth before choosing abstractions.
6. Choose a capability mode before planning files: small change, feature slice, frontend foundation, or prototype translation.
7. For small changes, identify the narrowest task scope, then decide whether new UI or logic belongs in the route file, the route's `components/`, `hooks/`, `data.ts`, or a shared abstraction.
8. For feature slices, early skeletons, or explicit "complete this module" requests, plan the coherent set of pages, routes, route-local components, hooks, mock/API modules, stores, scroll/list surfaces, empty/error/loading states, and navigation in one pass.
9. Apply this skill's rules only to newly added code or to existing code the user explicitly asked to modify.
10. Read only the references relevant to the current task.
11. Before finishing structural or layout refactors, run `pnpm type-check`, `pnpm lint`, and when the repo exposes a platform build script, a target build such as `pnpm build:mp-weixin`.

For WeChat Mini Program CI upload, preview QR, upload private key, `miniprogram-ci`, 上传开发版, or 上传体验版 requests, use `$wechat-miniprogram-ci-upload` instead of expanding this development skill.

## Non-Negotiables

- Do not proactively rewrite unrelated existing code to satisfy this skill.
- Do not create parallel wrappers when the project already has an equivalent request client, page shell, list controller, upload helper, feedback helper, realtime manager, or subscription helper.
- Do not turn project-specific brand prefixes, business nouns, headers, or protocols into generic conventions.
- Do not copy project-specific visual brands, route maps, business nouns, or component prefixes from a reference app into another app. Extract the reusable pattern and rename it to match the target repo.
- Do not hardcode local reference-project paths in generated code or skill guidance.
- Treat `App.vue` as the default `AppShell` layer for app-level lifecycle, global UI hosts, and global styles.
- Keep `App.vue` as a valid SFC shape; do not reduce it to style-only content because uni-app Vite builds require at least one `<script>` or `<template>` block.
- Do not reproduce the visual WeChat menu capsule from prototypes or design comps inside mini-program page UI; rely on the native system capsule and only align surrounding navigation around it when needed.
- Do not use raw characters such as `>`, `<`, `x`, or `X` as icon substitutes in UI text; use icon fonts or SVG assets instead.
- Unless the user explicitly asks for multi-platform behavior or the existing target requires it, do not add uni-app conditional compilation blocks such as `#ifdef`, `#ifndef`, or platform-specific branches. Default to the WeChat mini-program implementation.
- For newly added or user-requested modified mini-program `scroll-view` surfaces, default to `show-scrollbar="false"` and keep the global scrollbar suppression rule in `App.vue`; only keep visible scrollbars when the user explicitly asks for that behavior. Do not put horizontal page padding directly on vertical `scroll-view`; keep it on a full-width inner content `view` to avoid WeChat-side horizontal overflow.
- When the user provides a UI image, Figma, HTML prototype, or repo-local prototype page for a surface, treat that artifact as the visual source of truth; do not override it with generic skill defaults or template styling.
- When a repo is prototype-led or UI-first, learn from its page shell, tabbar mode, scroll structure, and route-local decomposition, but do not infer missing request, session, upload, realtime, or subscription layers as reusable conventions.
- Only when no UI source is provided should the implementation choose a default visual direction; in that case prefer a design that matches the current page and, when the task is visual, use the `frontend-design` skill guidance.
- Do not add active-state `translateY`, vertical lift, or similar positional displacement to tabbar items by default; only use that kind of motion when the user explicitly asks for a special interaction style.
- Use a shared generic `PageLayout` for all newly added route pages.
- Every confirmed uni-app mini-program project should have one shared global modal capability; reuse an existing global modal host and wrapper when present, otherwise add a shared `AppModal`, `modalStore`, and `useAppModal`.
- Keep startup pages, `tabBar` pages, and package-shared resources in the main package.
- When the app needs custom bottom tab navigation and can use Vue/Tailwind UI, default to a shared Vue tabbar mounted through the page shell instead of native `pages.json` `tabBar`; use official `custom-tab-bar/` only when the repo already uses it or the user explicitly asks for it.
- For newly added Vue SFCs, default to `Composition API` with `<script setup lang="ts">`.
- Default to local-first extraction: page-only UI goes in the owning route's `components/`; page-only orchestration goes in the owning route's `hooks/`; promote to shared layers only when reuse is cross-route and the abstraction can stay generic.
- For all newly added visible text, do not use a font size smaller than `20rpx`.
- Prefer generic names for new abstractions.
- Prefer one explicit vertical scroll surface per page region; avoid nested vertical `scroll-view`s unless the boundaries are deliberate and stable.
- Follow the scroll-height allocation rules: fixed sections use `shrink-0`, scroll parents use `min-h-0` or `h-0`, and sticky-plus-nested surfaces may require measured height.
- When defining custom Vue events in new code, use camelCase event names in `defineEmits` and `emit`, but consume them with hyphenated listeners in parent templates such as `@quick-action`.
- Use `pnpm` as the default package manager for dependency installation, script execution, and starter projects unless the user explicitly requires a different package manager.
- Git handling in this skill is limited to first-run repository initialization. For staging, commits, commit messages, push, or repository cleanup requests, use `$git-auto-commit`; for release promotion, cherry-pick, tags, or production branch publishing, use `$release-ops`.

## Capability Modes

### Small change mode
- Use this mode for isolated fixes, one-page changes, small visual adjustments, or narrow bug fixes.
- Keep the blast radius tight and follow the existing route/component style.
- Do not introduce new global abstractions unless the task actually needs them.

### Feature slice mode
- Use this mode when the user asks for a complete feature, page family, module, workflow, or several related pages.
- Read `references/feature-slice-delivery.md` before planning or editing.
- Deliver the frontend slice coherently: route entries, page-local components and hooks, route registration, mock/API adapters, stores when state is shared, scroll/list behavior, feedback states, and navigation handoff.
- Keep stable domain contracts in the repo's existing shared type layer when one exists; otherwise keep temporary display data route-local until transport is confirmed.

### Frontend foundation mode
- Use this mode when a confirmed uni-app repo is empty, early-stage, prototype-led, or missing repeated primitives needed by the requested work.
- Read `references/mature-miniapp-patterns.md` and the specific infrastructure references that apply.
- It is acceptable to add a generic `PageLayout`, one global modal capability, one request/session path, one app scroll/list path, and one tabbar path when the requested feature would otherwise duplicate those concerns.
- Reuse existing primitives first; only add missing foundation pieces that are directly needed by the requested feature.

### Prototype translation mode
- Use this mode when a local HTML prototype, Figma handoff, image, or mock page exists for the requested surface.
- Translate the visual hierarchy first, then choose the smallest component/hook split that keeps the implementation maintainable.
- Preserve the target repo's technical conventions and visual source of truth; do not substitute generic template styling unless the user asks for redesign.

## Build And Event Guardrails

- `type-check` and `lint` are not enough for uni-app refactors; platform builds can still fail on SFC-shape or compile-time integration issues, so run a real target build before concluding the task when possible.
- Keep `App.vue` minimal when needed, but preserve a non-empty `<script>` or `<template>` block so the Vue SFC compiler accepts it.
- For component events, prefer `defineEmits<{ (e: 'quickAction'): void }>()` in script and `@quick-action` in templates to satisfy both event-casing and listener-hyphenation lint rules.
- For WeChat official `custom-tab-bar/` in uni-app, create native mini-program files (`index.js`, `index.json`, `index.wxml`, `index.wxss`) under the project's source root `custom-tab-bar/` directory, not a Vue SFC such as `custom-tab-bar/index.vue`.
- For shared Vue tabbar mode, implement a normal Vue component such as `AppTabbar.vue`; do not use visual-shape terms as generic component names.

## Detect The Project First

Treat the repo as a confirmed uni-app mini-program project only when at least two strong signals are present, and at least one of them is framework-specific:

- `package.json` depends on `@dcloudio/uni-*`
- build config uses `@dcloudio/vite-plugin-uni` or another `@dcloudio` uni-app build plugin
- `manifest.json` or `src/manifest.json` exists
- `pages.json` or `src/pages.json` exists
- `App.vue` or `src/App.vue` exists

Supporting signals that may help but are not sufficient on their own:

- `src/pages` or multiple `pages*` directories exist
- Vue SFC route files are part of the runtime surface
- uni-app style platform APIs or conditional compilation are already present

Do not treat the repo as confirmed uni-app based only on signals that are common in native WeChat mini-program projects, such as:

- `app.json`, `app.js`, `app.wxss`, `project.config.json`
- `Page()` or `Component()` JavaScript pages with `.wxml` and `.wxss`
- `@vant/weapp`
- native `custom-tab-bar/`
- subpackages, `pages_v2`, or route folders by themselves

If the repo looks like a native WeChat mini-program rather than uni-app, do not use this skill unless the user explicitly asks for a uni-app scaffold or migration.

Treat the working directory as an empty bootstrap target when it contains no project files or only trivial files such as `.git`, `.gitignore`, `.DS_Store`, or editor metadata and the user explicitly asks to create a uni-app WeChat mini-program project.

If the repo is confirmed and `AGENTS.md` is missing at the root, create one immediately using the standard snippet in `references/activation-and-agents.md`.

If the repo is confirmed and the root is not a Git repository, initialize it with `git init`.

## Choose The Right Reference

- Read `references/architecture.md` for project layering and where new code belongs.
- Read `references/feature-slice-delivery.md` when implementing a complete feature, page family, workflow, or early-stage module rather than a single narrow edit.
- Read `references/mature-miniapp-patterns.md` when a repo needs frontend foundation patterns, when translating a mature reference implementation into generic target code, or when deciding how page shell, tabbar, scroll/list, request/session, feedback, and stores should fit together.
- Read `references/app-shell-and-page-layout.md` when adding or modifying route-level layout, navigation shells, bottom slots, or overlay hosts.
- Read `references/vue-best-practices.md` when adding or modifying Vue pages, components, or hooks.
- Read `references/project-bootstrap.md` when the user wants a new uni-app WeChat mini-program project created from an empty directory.
- Read `references/subpackage-strategy.md` when deciding whether a route belongs in the main package, a normal subpackage, an independent subpackage, or a preload flow.
- Read `references/page-recipes.md` when adding pages or page-level containers.
- Read `references/scroll-view-patterns.md` when adding or modifying `scroll-view`, native refresher flows, custom pull-refresh wrappers, anchored chat scroll, or horizontal scroll strips.
- Read `references/flex-layout-rules.md` when a page or component needs adaptive scroll height, sticky headers, fixed bottoms, drawers, or nested flex layout.
- Read `references/custom-tabbar.md` when adding or modifying bottom tab navigation, a custom tabbar component, tab badges, or cross-tab handoff state.
- Read `references/global-modal.md` when adding or modifying app-wide modal hosts, confirm flows, alert sheets, or bottom-sheet style global prompts.
- Read `references/tailwind-usage.md` for styling, sizing, and token rules.
- Read `references/icons-and-fonts.md` when adding icons, icon collections, icon classes, or font tokens.
- Read `references/auth-and-transport.md` for login, session, request wrappers, retries, and upload.
- Read `references/realtime-communication.md` for WebSocket, unread counts, or chat-like flows.
- Read `references/interaction-containers.md` for tabbed scroll areas, pull-to-refresh, load-more observers, or gesture conflicts.
- Read `references/custom-wrappers.md` when deciding whether to add a new hook, util, or wrapper.
- Read `references/third-party-usage.md` before adding or expanding dependency usage.
- Read `references/message-subscription.md` for WeChat subscription-message flows.
- Read `references/wechat-adaptation.md` for sharing, menu button, permissions, safe area, or mini-program-only behavior.
- Read `references/decoupling-rules.md` when extracting reusable abstractions from business code.

## Deliver New Work By Task Type

### Create a new project from an empty directory
- Scaffold from `assets/templates/project-starter/`.
- Use the current folder name as the default package name when no name is given.
- Initialize Git immediately after scaffolding when the target is not already a Git repository.
- Create the root `AGENTS.md` immediately after scaffolding.
- Keep the starter generic, WeChat-first, Tailwind-first, and free of business naming.
- Treat starter `App.vue` as the default `AppShell` layer and include a shared generic `PageLayout`.
- Include a shared global modal host in starter `App.vue`, plus starter `modalStore` and `useAppModal`.
- Do not scaffold bottom tab navigation in a starter unless the user asks for it; when requested and the project uses Tailwind/Iconify, scaffold a shared Vue `AppTabbar` instead of official `custom-tab-bar/`.
- Keep the starter on a single main package by default; add subpackages only when the user asks for a larger information architecture or the new routes clearly need package-level separation.
- Do not add optional business wrappers until the user asks for them.

### Add a new page
- Use the page recipe that matches the task.
- Decide whether the route belongs in the main package, a normal subpackage, or an independent subpackage before creating it.
- Use the shared `PageLayout` for every newly added route page.
- Default to `Composition API` with `<script setup lang="ts">` for new route SFCs.
- If the repo includes a route-matched prototype HTML page, image, or local mock for the surface, translate that artifact into the route shell first and keep the page visually faithful unless the user asks for redesign.
- Choose the lightest scroll strategy that satisfies the page before writing the page body: plain `scroll-view`, native refresher list, shared custom scroll wrapper, tabbed container, or anchored chat scroll.
- Start from `page-with-local-hooks/` when the page already needs route-local `components/` plus `hooks/`.
- Put route-only child UI in the route's `components/` directory.
- Put route-only orchestration in the route's `hooks/` directory.
- Keep route-local static display data or prototype data in the owning route folder, such as `data.ts`, until real transport or cross-route reuse is required.
- Reuse the repo's existing page shell and feedback patterns when they already match the `PageLayout` role.
- Reuse existing list, upload, share, or subscription helpers before adding new ones.
- Reuse the repo's icon and font-token setup instead of adding a parallel icon/font system.
- Keep all new visible text at `20rpx` or above.

### Add or modify subpackages
- Reuse the repo's existing `subPackages` or `subpackages` structure before inventing a new layout.
- Keep startup pages, `tabBar` pages, and package-shared resources in the main package.
- Use normal subpackages for low-frequency or feature-cluster routes that do not belong in the startup path.
- Use independent subpackages only for highly independent, high-startup-priority flows such as campaign landing pages, payment-like flows, or ad entry pages.
- Add `preloadRule` only from high-probability entry pages to high-probability next packages; default `network` to `wifi` unless the user explicitly wants broader preload behavior.
- Keep cross-package shared code in main-package shared layers instead of making one subpackage depend on another.

### Add or modify Vue pages, components, or hooks
- Keep the route entry thin: route params, lifecycle hooks, share hooks, and page-level orchestration.
- Extract page-owned UI blocks into that route's `components/` directory when they have a stable visual or interaction boundary.
- Extract page-owned orchestration into that route's `hooks/` directory when it manages lifecycle, local state, or platform coordination for one route.
- Keep route-local static content, prototype-derived arrays, or display-only mock data in the owning route folder before promoting them to a store or shared module.
- Promote code to `src/components` or `src/hooks` only after it is reused across routes or is clearly generic and stable.
- Keep presentational components driven by props, emits, and explicit slots; keep transport IO, stores, and business-only mapping outside them.
- When child components emit custom events, declare the event names in camelCase in script and listen with hyphenated attributes in templates.

### Add or modify scroll surfaces
- Read `references/scroll-view-patterns.md` and `references/flex-layout-rules.md` first.
- Choose among plain `scroll-view`, native `refresher-*`, shared custom scroll wrapper, tabbed scroll container, and anchored chat scroll before writing the implementation.
- Use native `refresher-*` only for simple refresh flows with platform-default or lightly customized visuals.
- Use a shared custom scroll wrapper when the page needs a custom refresh indicator, refresh plus load-more coordination, top-detection tolerance, or stronger gesture control.
- Use `scroll-into-view` first for chat-like anchored scroll, and add `scroll-top` only as a fallback or force-scroll path.
- Put safe-area bottom padding on the inner scroll content layer instead of the outer page shell.
- Put horizontal page padding on an inner `view` such as `box-border w-full px-[...]`, not directly on a vertical `scroll-view`; in WeChat mini-program builds, padding on `scroll-view` can make children render wider than the viewport and clip right-aligned content.
- Keep one vertical scroll surface per region when possible; do not stack nested vertical `scroll-view`s unless the visual regions are explicit and independently scrollable.
- Follow the height rules in `references/flex-layout-rules.md`: fixed sections use `shrink-0`, ancestor shrink paths use `min-h-0`, direct scroll slots often use `flex-1 h-0`, and sticky-plus-nested surfaces may require measured height.

### Add or modify custom tabbar
- Reuse the repo's current bottom-navigation pattern before introducing a new one.
- If the repo already has Tailwind/Iconify icons, a shared `PageLayout`, or the user asks for a Vue component tabbar, default to a shared Vue `AppTabbar` mounted through the page shell.
- If the repo already has a thin tab-page wrapper over `PageLayout`, extend that wrapper instead of mounting the shared tabbar separately inside every tab page.
- Use official `custom-tab-bar/` only when the repo already uses it, the user explicitly asks for it, or native mini-program tabbar lifecycle integration is required.
- If the repo only has native `pages.json` `tabBar` and the user asks for class-based icons or custom UI, migrate to shared Vue tabbar by default instead of trying to force class icons into native `tabBar`.
- Keep tab routes in `pages.json` as the source of truth and mirror them through typed config only when a custom tabbar component needs it.
- In official `custom-tab-bar/` mode, keep route ownership in `pages.json` and keep the tabbar UI, badges, and active-state mapping inside the custom tabbar layer.
- In uni-app WeChat projects, implement official `custom-tab-bar/` with native mini-program files in the source-root `custom-tab-bar/` directory; do not implement it as a Vue page or Vue component.
- Only stay in native `tabBar` mode when the user explicitly requires it; in that case, use local icon assets instead of class-based icon names.
- Keep unread badges, red dots, and cross-tab handoff state in a store instead of page-local patches.
- Mount shared custom tabbar content through `PageLayout` bottom slots instead of hardcoding it into the layout base.
- Treat standard bottom bars, floating capsules, raised center buttons, and other visual shapes as style variants, not as generic architecture names.
- Do not hardcode project-specific center actions, labels, or business routing into a generic tabbar base.

### Add or modify global modal flows
- Every uni-app mini-program project should expose one shared global modal capability.
- Reuse the repo's existing global modal host, store, and hook when they already exist and are coherent.
- If the repo lacks a shared global modal, add a style-neutral `AppModal` host, a shared `modalStore`, and a `useAppModal` hook.
- Mount the global modal host in `App.vue` or the repo's existing `AppShell`; keep `PageLayout` free of required global modal hosts in new code.
- Support both `center` and `bottom` placement in the shared global modal capability.
- Keep the shared modal string-first and promise-driven for confirm, alert, and simple sheet flows; keep complex business forms or custom markup in page-local or feature-local components.
- For new code, prefer the shared modal wrapper over raw `uni.showModal` unless the platform API itself must own the confirmation UI.
- Keep the shared modal behavior style-neutral; allow project wrappers or classes to restyle it without renaming the generic abstraction.

### Add or modify request/auth flows
- Reuse the existing request wrapper if present.
- Keep login/session state inside a store.
- Keep endpoint IO in `api` modules and orchestration in stores or hooks.
- Parameterize project-specific headers, signing, handshake, and ban-state logic rather than baking them into a generic abstraction.

### Add realtime features
- Use a single app-level WebSocket manager.
- Bind page handlers on `onShow` and unbind on `onHide` or `onUnload`.
- Add polling fallback only for state that must stay fresh when push is missing.

### Add complex interaction containers
- Use the simplest scroll container that satisfies the task.
- Escalate to a tabbed interaction container only when a page truly needs independent tab state, horizontal swipe, pull-to-refresh, and load-more in the same surface.
- Keep direction-lock, refresh-control, and observer logic separated even if the final component composes them together.
- Prefer measured container height over ever-deeper flex chains when sticky headers, swipe tracks, drawers, or nested scroll surfaces share one page.

### Add message subscriptions
- Keep template mapping configurable.
- Request no more than three templates per `uni.requestSubscribeMessage` call.
- Refresh status after every request.
- Guide the user to settings when they previously rejected a template.

## Templates

Use the thin templates in `assets/templates/` only as starting points. Replace generic wrapper names with the repo's existing equivalents whenever they already exist.

Available templates:
- `project-starter/`
- `page-with-local-hooks/`
- `app-modal.vue`
- `app-scroll.vue`
- `app-tabbar.vue`
- `modal-store.ts`
- `page-layout.vue`
- `pull-refresh-indicator.vue`
- `request-client.ts`
- `session-store.ts`
- `tabbar-config.ts`
- `use-app-modal.ts`
- `paged-list-page.vue`
- `form-page.vue`
- `use-anchored-scroll.ts`
- `use-load-more-observer.ts`
- `use-refresh-pull.ts`
- `websocket-client.ts`
- `use-realtime-events.ts`
- `tab-scroll-container.vue`
- `use-subscription.ts`
- `subscription-center.vue`
- `feature-slice-page.vue`
- `use-paged-list.ts`

## Defaults

- Default to `App.vue` as `AppShell` and `PageLayout` as the shared route layout layer.
- Default to one shared global modal host in `AppShell`, backed by a shared modal store and hook.
- Default to WeChat mini-program behavior when a platform-specific choice is required.
- Default custom bottom tab navigation to shared Vue tabbar mode when Tailwind/Iconify or Vue component UI is available; preserve official `custom-tab-bar/` only for existing usage, explicit requests, or lifecycle-specific needs.
- Default to Tailwind-first styling.
- Default to `Composition API` with `<script setup lang="ts">` in newly added Vue SFCs.
- Default to page-local components and hooks before promoting code to `src/components` or `src/hooks`.
- Default to route-local `data.ts` or nearby local modules for prototype-derived static content before introducing shared stores or transport-driven data flow.
- Default to prototype translation before visual redesign when the repo already includes route-matched local prototypes or mock pages.
- Default to store-driven session state and wrapper-driven network IO.
- Default scroll height adaptation to `flex-1 min-h-0` shells with direct scroll slots such as `flex-1 h-0`, and escalate to measured height only when the layout proves brittle.
- Default to preserving existing code unless the user asked to change it.
