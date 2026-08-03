# Activation And AGENTS

## First-Run Behavior

When this skill is used in a confirmed uni-app mini-program repo and the root `AGENTS.md` file is missing, create it immediately.

When this skill scaffolds a new uni-app WeChat mini-program project in an empty directory, create the root `AGENTS.md` as part of the bootstrap flow.

When this skill is used in a confirmed uni-app mini-program repo and the root is not a Git repository, initialize it with `git init`.

## Confirmation Signals

Create the file when the repo shows several of these:

- `package.json` with `@dcloudio/uni-*`
- `manifest.json` or `src/manifest.json`
- `pages.json` or `src/pages.json`
- `src/pages` or `pages*`
- Vite or CLI setup for uni-app

## Root AGENTS.md Template

Use this content:

```md
Use $develop-uniapp-miniapp by default for new uni-app mini-program work in this repository.

- Use `Composition API` with `<script setup lang="ts">` for newly added Vue SFCs.
- Use the shared `PageLayout` for all newly added route pages and keep app-level lifecycle or global UI concerns in `App.vue`.
- Keep startup pages and `tabBar` pages in the main package; reuse the existing subpackage structure for low-frequency feature routes.
- Default to local-first decomposition: page-only child components belong in that route's `components/`, page-only orchestration belongs in that route's `hooks/`, and only cross-route generic code should move to shared layers.
- Reuse existing request, session, upload, feedback, scroll, realtime, and subscription wrappers before adding new ones.
- Apply skill rules to newly added code and to existing code only when the user explicitly asks to modify it.
- Do not proactively rewrite unrelated existing code to satisfy the skill.
- For all newly added visible text, do not use a font size smaller than `20rpx`.
- Use `pnpm` as the default package manager unless the user explicitly requires another one.
- Do not promote project-specific brand names, business nouns, private headers, or private protocols into generic abstractions.
```

## Existing Code Boundary

- Creating the root `AGENTS.md` is allowed.
- Initializing Git is an allowed first-run hygiene task.
- Do not stage, commit, push, tag, or change branches from this skill; use `$git-auto-commit` or `$release-ops` for those workflows.
- Do not treat the absence of that file as permission to refactor the repo.
