# Global Modal

## Requirement

- Every confirmed uni-app mini-program project should expose one shared global modal capability.
- Reuse an existing global modal system when the repo already has one coherent host plus state layer.
- If the repo lacks a shared global modal, add a shared `AppModal`, `modalStore`, and `useAppModal`.

## Ownership

- Mount the global modal host in `App.vue` or the repo's existing `AppShell`.
- Keep required global modal hosts out of `PageLayout` in new code.
- If an existing repo already mounts a stable global modal in `PageLayout`, do not migrate it unless the user asks; avoid adding a second host.

## Interface

- Support `center` and `bottom` placement.
- Return a promise result such as `{ confirm, cancel }` from the shared modal wrapper.
- Keep the shared global modal string-first for title and content.
- Use page-local or feature-local components when the modal body needs custom forms, heavy markup, payment logic, or route-owned orchestration.
- Keep modal option names generic, for example `title`, `content`, `placement`, `showCancel`, `showConfirm`, `maskClosable`, and `maxHeight`.

## Style Decoupling

- Do not bind the shared modal contract to a visual style name or business theme.
- Provide only a minimal usable default shell in generic templates.
- Let projects restyle the shell through tokens, wrapper components, static classes, or style overrides.
- If a project passes Tailwind class-name overrides dynamically, keep those classes literal in scanned files or safelist them.

## When To Use

- confirm and cancel prompts
- alert or warning dialogs
- simple information dialogs
- simple bottom sheets with short explanatory text or actions

## When To Keep It Local

- complex forms
- selectors with rich page-owned state
- payment panels
- media pickers
- modal bodies that depend on feature-local slots or large custom markup

## Existing Code Boundary

- Do not rewrite unrelated existing modal usage unless the user asks.
- For new code, prefer the shared modal wrapper over raw `uni.showModal` when a reusable app-level prompt is appropriate.
