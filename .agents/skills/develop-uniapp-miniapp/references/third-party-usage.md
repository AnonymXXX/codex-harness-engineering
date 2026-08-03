# Third-Party Usage

## Core Dependencies

### Package Manager

- Use `pnpm` by default for dependency installation and script execution.
- Prefer `pnpm install`, `pnpm dev:mp-weixin`, `pnpm build:mp-weixin`, `pnpm type-check`, and `pnpm lint`.
- Only follow another package manager if the existing repo is already committed to it or the user explicitly requests it.

### Pinia

- Use Pinia for session state, shared unread state, app-wide UI state, or other cross-route state.
- Keep transport IO out of components even when Pinia owns the resulting state.

### uni-app Lifecycle APIs

- Use explicit lifecycle hooks from `@dcloudio/uni-app` in route-level or lifecycle-sensitive hooks.
- Keep `onLoad`, `onShow`, `onHide`, `onUnload`, `onShareAppMessage`, and `onShareTimeline` close to the route that owns them.

### TypeScript Config

- Prefer `compilerOptions.paths` without `compilerOptions.baseUrl` for `@/`-style aliases.
- Treat `ignoreDeprecations` as a temporary silencing fallback, not the default fix for `baseUrl` deprecation.
- When updating a repo's TypeScript config, remove `baseUrl` first if it only exists to support `paths`.

### Tailwind And weapp-tailwindcss

- Treat Tailwind as the default UI authoring method.
- Respect the existing `weapp-tailwindcss` pipeline when the repo uses it.

### Tailwind/Iconify Icons

- Prefer `@egoist/tailwindcss-icons` with Iconify collection packages for generic class-based icons.
- Register icon collections centrally in `tailwind.config.ts`; do not import or copy SVG paths in individual pages unless custom artwork is required.
- Add only the collection required by the feature using `pnpm add -D @iconify-json/<collection>`.
- In mini-program builds, keep the shared mask-size/mask-position/mask-repeat fix for `[class^="i-"]` and `[class*=" i-"]`.

### Dayjs

- Use a shared formatting helper or local formatting util for date display, countdowns, and relative labels.
- Avoid scattered custom date parsing logic across pages.

## Optional Dependencies

### CryptoJS

- Use only when the project already needs request signing or hashing.
- Keep it inside low-level transport helpers.

### vue-i18n

- Only use it when the repo already has an active internationalization setup.
- Do not introduce it as a default requirement for a mono-language mini-program.

## Dependency Discipline

- Do not add a new library when existing project wrappers already solve the problem.
- Prefer wrapping platform APIs before introducing general-purpose third-party abstractions.
- If a component, plugin, or heavy dependency is only used in one subpackage, avoid global registration and keep the import local to that package path when possible.
- Avoid unnecessary global `usingComponents` or global plugin registration in `app.json`; they increase startup download or injection cost and weaken subpackage benefits.
- In new starter projects created by this skill, set `packageManager` to the current `pnpm -v` result using full semver, such as `pnpm@10.18.2`; avoid major-only values like `pnpm@10`.
