# Project Bootstrap

## When To Use

Read this file when the working directory is empty or near-empty and the user asks to create a uni-app WeChat mini-program project from scratch.

## Empty Directory Rule

Treat the directory as bootstrap-ready when it has no project files or only trivial files such as:

- `.git`
- `.gitignore`
- `.DS_Store`
- editor metadata

If project files already exist, do not overwrite them blindly. Switch to extension mode instead.

## Bootstrap Steps

1. Copy `assets/templates/project-starter/` into the working directory.
2. Rename the package name to match the directory name if the user did not provide one.
3. Keep the app generic and WeChat-first.
4. Create the root `AGENTS.md` immediately using `references/activation-and-agents.md`.
5. After scaffolding, treat the directory as a normal uni-app mini-program repo and follow the rest of this skill.
6. Install dependencies with `pnpm`, and prefer `pnpm` for all subsequent script execution.

## Starter Scope

The starter should include:

- `package.json`
- `pnpm-lock.yaml` after installation
- `vite.config.ts`
- `tsconfig.json`
- `postcss.config.js`
- `tailwind.config.ts`
- Tailwind/Iconify icon support with a generic starter icon collection
- `eslint.config.mjs`
- `index.html`
- `src/main.ts`
- `src/App.vue`
- `src/components/AppModal.vue`
- `src/components/PageLayout.vue`
- `src/hooks/useAppModal.ts`
- `src/pages.json`
- `src/manifest.json`
- `src/stores/modal.ts`
- `src/uni.scss`
- `src/pages/index/index.vue`
- minimal type declarations

## Starter Rules

- Keep the starter minimal and runnable.
- Keep the starter Tailwind-first.
- Keep the starter icon/font setup generic and centralized.
- In starter `tsconfig.json`, prefer `paths` aliases without `compilerOptions.baseUrl`.
- Use `Composition API` with `<script setup lang="ts">` in starter Vue SFCs that need script logic.
- Keep `App.vue` focused on `AppShell` responsibilities such as app lifecycle, global styles, and global UI hosts.
- Include a shared style-neutral global modal host in starter `App.vue`.
- Keep route layout concerns in the shared `PageLayout`.
- When starter routes grow beyond a single file, put page-local child UI in the route's `components/` directory and page-local orchestration in the route's `hooks/` directory.
- Keep the starter on a single main package by default; do not scaffold `subPackages` until the user asks for a larger route architecture or a new feature clearly warrants package separation.
- Keep all new visible text at `20rpx` or above.
- Do not preload business abstractions that are not needed for a fresh project.
- Do include the shared global modal capability in the starter because it is a default app-shell primitive rather than a business abstraction.
- Do not scaffold a custom tabbar by default; add it only when the user asks for bottom-navigation customization.
- When the user asks for custom bottom navigation in a starter, scaffold a shared Vue `AppTabbar` with Tailwind/Iconify class icons and keep `pages.json` `tabBar.custom: true`.
- If the user asks for native tabbar behavior instead, use local `iconPath` and `selectedIconPath` assets rather than class-based icon names.
- Use generic naming only.
- Set `packageManager` in `package.json` to the current `pnpm -v` result using full semver, such as `pnpm@10.18.2`; do not use a major-only value like `pnpm@10`.

## Existing Code Boundary

- Do not use bootstrap mode in non-empty projects unless the user explicitly asks to replace the project.
