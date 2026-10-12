---
name: develop-uniapp-miniapp
description: Build, scaffold, and extend uni-app (Vue 3) WeChat mini-program frontends with a Tailwind-first, local-first workflow. Use for page changes, complete feature slices, frontend foundation (page shell, modal, request/session, scroll/list, tabbar, subpackages), and prototype-to-miniapp work in confirmed uni-app repos, or when the user asks to create or migrate to uni-app. Do not use for native WeChat mini-program repos (`app.json`, `Page()`, `.wxml`) without uni-app markers.
---

# Develop Uniapp Miniapp

Deliver uni-app mini-program frontend work, from narrow fixes to complete feature slices, without rewriting unrelated existing code.

## Detect The Project First

Treat the repo as confirmed uni-app only when at least two strong signals are present and at least one is framework-specific:

- `package.json` depends on `@dcloudio/uni-*`
- the build config uses `@dcloudio/vite-plugin-uni` or another `@dcloudio` build plugin
- `manifest.json` or `src/manifest.json` exists
- `pages.json` or `src/pages.json` exists
- `App.vue` or `src/App.vue` exists

Native WeChat signals (`app.json`, `app.js`, `project.config.json`, `Page()`/`Component()` with `.wxml`/`.wxss`, `@vant/weapp`, native `custom-tab-bar/`, subpackage folders) do not confirm uni-app. For a native repo, stop using this skill unless the user explicitly asks for a uni-app scaffold or migration.

An empty target (no files, or only `.git`, `.gitignore`, `.DS_Store`, editor metadata) plus an explicit create request means bootstrap mode; see `references/project-bootstrap.md`.

## Workflow

1. Confirm the project type with the detection rules above.
2. Read the root agent instructions (`AGENTS.md`, `CLAUDE.md`) and `DESIGN.md` when present. Create instruction files only for requested bootstrap or documentation work; see `references/activation-and-agents.md`.
3. If a prototype, HTML mock, image, or Figma handoff exists for the surface, it is the visual source of truth.
4. Choose a capability mode (below), then read only the references that task needs.
5. Apply these rules to new code and to existing code the user asked to change.
6. Before finishing, run the project's `type-check` and `lint` scripts with its package manager, plus a real target build such as `pnpm build:mp-weixin`. Type-check and lint alone miss SFC-shape and compile-time integration failures.

## Capability Modes

- **Small change**: isolated fix, one page, or a visual tweak. Keep the blast radius tight, follow the existing route style, and add no global abstractions.
- **Feature slice**: a complete feature, page family, workflow, or "finish this module". Read `references/feature-slice-delivery.md` and deliver routes, route-local components/hooks, mock/API adapters, shared stores, scroll/list behavior, loading/empty/error states, and navigation together.
- **Frontend foundation**: an empty, early, or prototype-led repo that lacks primitives the requested work needs. Read `references/mature-miniapp-patterns.md`. Reuse existing primitives first, and add only the missing pieces (`PageLayout`, one global modal, one request/session path, one scroll/list path, one tabbar path) that the feature directly needs.
- **Prototype translation**: translate the artifact's visual hierarchy first, then choose the smallest component/hook split that stays maintainable. Do not substitute template styling unless the user asks for a redesign.

## Hard Rules

**Scope and reuse**
- Do not rewrite unrelated existing code to satisfy this skill.
- Reuse the repo's existing request client, page shell, list controller, upload/feedback helpers, realtime manager, modal, and subscription helpers instead of adding parallel wrappers.
- Do not turn project-specific brands, business nouns, headers, protocols, route maps, or component prefixes into generic conventions, and do not hardcode reference-project paths.
- Preserve the declared package manager and lockfile; use `pnpm` only for a new project with no established choice.

**Structure**
- New Vue SFCs use `<script setup lang="ts">`.
- Local-first: page-only UI goes in the route's `components/`, page-only orchestration in its `hooks/`, and static or prototype data in its `data.ts`. Promote code to `src/components` or `src/hooks` only when it is reused across routes and stays generic.
- `App.vue` is the `AppShell` for app lifecycle, global styles, and global UI hosts. It must keep a non-empty `<script>` or `<template>` block.
- New route pages use the shared `PageLayout`, or the repo's existing shell when that already fills the role.
- Keep at most one global modal capability. Reuse the existing one; add `AppModal` + `modalStore` + `useAppModal` only when the requested work needs app-wide prompts.
- Keep startup pages, `tabBar` pages, and package-shared resources in the main package.
- Custom events are declared in camelCase in script (`emit('quickAction')`) and listened to with hyphens in templates (`@quick-action`).

**Mini-program UI**
- Default to WeChat behavior. Add no `#ifdef`/`#ifndef` or platform branches unless multi-platform is requested or already required.
- Do not draw the WeChat menu capsule in page UI; align surrounding navigation around the native capsule.
- Use icon fonts or SVG for icons, never raw characters like `>`, `<`, or `x`.
- Visible text is at least `20rpx`.
- New `scroll-view`s use `show-scrollbar="false"`. Put horizontal padding on an inner full-width `view`, not on a vertical `scroll-view` (that overflows in WeChat). Keep one vertical scroll surface per region.
- Height chains: fixed sections use `shrink-0`, scroll parents `min-h-0`, direct scroll slots `flex-1 h-0`. Use measured height for sticky-plus-nested layouts.
- Do not add `translateY` lift to active tabbar items unless asked.
- Custom bottom navigation defaults to a shared Vue `AppTabbar` mounted through the page shell. Use official `custom-tab-bar/` (native files, not `.vue`) only when the repo already uses it or the user asks.
- With no UI source, match the current page; for visual-heavy tasks use `frontend-design`.

**Delegation**
- CI upload, preview QR, or 体验版/开发版 upload: use `wechat-miniprogram-ci-upload`. Commits and pushes: `git-auto-commit`. Release promotion and tags: `release-ops`.
- Initialize Git only for a requested bootstrap or Git setup.

## References

| Task | Read |
|---|---|
| Layering and where new code belongs | `references/architecture.md` |
| Complete feature or page family | `references/feature-slice-delivery.md` |
| Foundation patterns from mature apps | `references/mature-miniapp-patterns.md` |
| New project from an empty directory | `references/project-bootstrap.md`, `references/activation-and-agents.md` |
| App shell, `PageLayout`, bottom slots, overlay hosts | `references/app-shell-and-page-layout.md` |
| Adding pages (list, form, detail, chat, tabbed) | `references/page-recipes.md` |
| Vue pages, components, hooks, events | `references/vue-best-practices.md` |
| Main package vs subpackage vs independent, preload | `references/subpackage-strategy.md` |
| `scroll-view`, refresher, anchored chat scroll | `references/scroll-view-patterns.md`, `references/flex-layout-rules.md` |
| Tabbed scroll, pull-refresh, load-more, gestures | `references/interaction-containers.md` |
| Bottom navigation, badges, `custom-tab-bar/` | `references/custom-tabbar.md` |
| Global modal, confirm, bottom sheet | `references/global-modal.md` |
| Tailwind, sizing, tokens | `references/tailwind-usage.md` |
| Icons and fonts | `references/icons-and-fonts.md` |
| Login, session, request, retry, upload | `references/auth-and-transport.md` |
| WebSocket, unread counts, chat | `references/realtime-communication.md` |
| Subscription messages | `references/message-subscription.md` |
| Share, capsule, permissions, safe area, platform | `references/wechat-adaptation.md` |
| New hook, util, or wrapper | `references/custom-wrappers.md`, `references/decoupling-rules.md` |
| Adding dependencies | `references/third-party-usage.md` |

## Templates

`assets/templates/` holds thin starting points. Rename them to the repo's existing equivalents when those already exist.

- `project-starter/` is a runnable starter and the canonical source for `App.vue`, `PageLayout.vue`, `AppModal.vue`, `stores/modal.ts`, and `hooks/useAppModal.ts`; copy those files from here when an existing repo needs them.
- `page-with-local-hooks/` is a route with local `components/` and `hooks/`.
- Pages: `feature-slice-page.vue`, `paged-list-page.vue`, `form-page.vue`, `subscription-center.vue`.
- Scroll and lists: `app-scroll.vue`, `pull-refresh-indicator.vue`, `tab-scroll-container.vue`, `use-paged-list.ts`, `use-load-more-observer.ts`, `use-refresh-pull.ts`, `use-anchored-scroll.ts`.
- Navigation: `app-tabbar.vue`, `tabbar-config.ts`.
- Transport and state: `request-client.ts`, `session-store.ts`, `websocket-client.ts`, `use-realtime-events.ts`, `use-subscription.ts`.

## Maintaining This Skill

After editing anything under `assets/templates/`, run `scripts/check-templates.sh`. It scaffolds the starter into a temp directory, adds the standalone templates, and requires `build:mp-weixin`, `type-check`, and `lint` to pass. uni-app currently pins Vite 5.2.8, so `unplugin-vue-components` 32 (ESM-only) and `weapp-tailwindcss` 5 (renamed exports) need a migration before they can be upgraded.
