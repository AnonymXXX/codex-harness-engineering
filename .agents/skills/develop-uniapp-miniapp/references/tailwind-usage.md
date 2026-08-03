# Tailwind Usage

## Core Rules

- Use Tailwind classes for layout, spacing, sizing, color, typography, border, radius, opacity, and shadow by default.
- Keep `uni.scss` minimal and reserved for framework variables or unavoidable global compatibility rules.
- Put repeated colors, shadows, fonts, spacing tokens, animations, and safe-area helpers in `tailwind.config.ts`.
- Use scoped CSS only for complex animation, keyframes, pseudo-element work, clip-path, mask effects, or platform-specific compatibility hacks.

## Mini-Program Specifics

- Treat `weapp-tailwindcss` as part of the standard toolchain when the repo already uses it.
- Prefer `rpx`-based arbitrary values for one-off sizing such as `px-[24rpx]`.
- When a value repeats, promote it into a reusable token instead of repeating arbitrary values across files.
- Keep icon usage consistent with the repo's icon pipeline when one already exists.

## Layout Skeletons

- Fixed headers, filter bars, tab rows, and bottom actions usually use `shrink-0`.
- Ancestors that must allow a scroll region to shrink usually use `min-h-0`.
- The direct slot that hands remaining height to a `scroll-view` usually uses `flex-1 h-0`.
- Flexible text columns inside horizontal rows usually use `min-w-0`.
- Scroll shells usually use `overflow-hidden`.

## Scroll Surface Classes

- For vertical main content, prefer shells such as `flex-1 min-h-0 flex flex-col overflow-hidden`.
- For the direct scroll slot, prefer classes such as `flex-1 h-0`.
- For the `scroll-view` itself, prefer classes such as `h-full w-full box-border overflow-hidden`.
- Put safe-area bottom spacing on the inner scroll content layer with tokens such as `pb-safe`.
- For horizontal strips, use `whitespace-nowrap`, `inline-flex`, or `shrink-0` items so the content does not wrap unexpectedly.
- Hide scrollbars only when another affordance still communicates overflow.

## Typography

- All newly added visible text must use `20rpx` or larger.
- Use `20rpx` for the smallest helper text, counter text, and metadata.
- Use `24rpx` and above for standard body text.
- Do not introduce new text styles below `20rpx` even for badges or secondary labels.

## Token Guidance

- Reuse existing semantic tokens before adding new ones.
- Prefer semantic names over business names.
- Do not add a second color system when the repo already has one.

## Existing Code Boundary

- Do not proactively rewrite existing pages that use smaller font sizes or mixed CSS patterns.
- Apply these rules to newly added code or to user-specified edits only.
