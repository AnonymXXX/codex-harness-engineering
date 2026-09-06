# Activation And AGENTS

## Creation Boundary

Read existing root `AGENTS.md` before editing. For an existing project, create missing instructions only when requested or when the Harness Capture Gate passes; skill activation alone does not authorize a document or repository initialization.

For an explicitly requested new uni-app WeChat mini-program bootstrap, create a minimal root `AGENTS.md` and initialize Git when the directory is not already part of a repository. Confirm the framework using the detection rules in [SKILL.md](../SKILL.md#detect-the-project-first); do not infer uni-app from native WeChat files alone.

## Root AGENTS.md Template

Adapt this template to confirmed project conventions; do not copy defaults that contradict an existing framework, package manager, or layout:

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
- Preserve the declared package manager and lockfile; use `pnpm` only for a new project without an established choice.
- Do not promote project-specific brand names, business nouns, private headers, or private protocols into generic abstractions.
```

## Existing Code Boundary

- Apply the creation boundary above; existing-project edits do not require bootstrap side effects.
- Do not stage, commit, push, tag, or change branches from this skill; use `$git-auto-commit` or `$release-ops` for those workflows.
- Do not treat the absence of that file as permission to refactor the repo.
