# Icons And Fonts

## Default Icon Strategy

- Prefer Tailwind/Iconify class icons for uni-app mini-program projects.
- Use a Tailwind icon plugin to generate icon classes such as `i-fa6-solid-house`.
- Size and color icons with Tailwind classes, for example `text-[24rpx] text-ui-muted`.
- Keep icon names as presentation details in UI config or component props.
- Do not use raw characters such as `>`, `<`, `x`, or `X` as icon stand-ins for more, close, back, expand, or similar UI affordances.
- When the UI needs those affordances, use a font icon or SVG asset, for example `i-fa6-solid-angle-right`, `i-fa6-solid-xmark`, or `i-fa6-solid-arrow-left`.

## Mini-Program Icon Fix

Mini-program builds may render mask-based icons incorrectly unless mask utilities are normalized.

Add a small Tailwind plugin that applies these rules to icon classes:

- `mask-size: contain`
- `-webkit-mask-size: contain`
- `mask-position: center`
- `-webkit-mask-position: center`
- `mask-repeat: no-repeat`
- `-webkit-mask-repeat: no-repeat`

Apply the fix to selectors matching icon class usage, including `[class^="i-"]` and `[class*=" i-"]`.

## Adding Icon Collections

- Add only the icon collection needed by the feature.
- Use `pnpm` for new icon dependencies.
- Register collections centrally in `tailwind.config.ts`.
- Do not scatter SVG paths or copied icon assets across pages unless the product explicitly requires custom artwork.

## Starter Defaults

- New starter projects include `@egoist/tailwindcss-icons` and `@iconify-json/fa6-solid` as a generic baseline.
- Keep the starter collection small; add more collections only when a feature needs them.
- Use a simple icon sample on the initial page to prove the Tailwind/Iconify pipeline works.

## Dynamic Icons

- If a component receives an icon prop, store the icon class string.
- Keep the icon class generic and presentation-focused.
- Do not encode business workflow rules into icon names.
- Keep dynamic icon class strings as literals in files included by Tailwind content scanning, such as a tabbar config module, or add an explicit safelist.
- Do not build icon class names through string concatenation unless the generated classes are safelisted.

## Tabbar Icon Exception

- Native `pages.json` `tabBar` does not consume Tailwind/Iconify class names; use local `iconPath` and `selectedIconPath` assets there.
- Tailwind/Iconify class icons remain the default for shared Vue tabbar components, page content, and other Vue UI.
- If the user wants a Vue component tabbar or class-based icon names such as `i-fa6-solid-house`, prefer shared Vue tabbar mode instead of native `tabBar`.
- If a repo stays on native `tabBar`, plan tabbar image assets explicitly instead of assuming the page icon pipeline can be reused directly.
- Do not bind the shared Vue tabbar guidance to one visual shape; standard bottom bars and more expressive variants can use the same icon pipeline.

## Font Strategy

- Expose fonts through `tailwind.config.ts` `fontFamily` tokens.
- Use generic token names such as `sans`, `mono`, `display`, or `number`.
- Keep `@font-face` declarations in a single global style entry or dedicated global style file.
- Do not scatter raw font-family names across pages.
- Do not bake product-specific font names or visual themes into reusable skill guidance.

## Font Assets

- Prefer project-owned font assets under the repo's static asset convention when custom fonts are required.
- Keep font loading global and token-based; components should use Tailwind font tokens instead of raw font-family strings.
- Use remote, embedded, or base64 fonts only when the project already chose that delivery strategy or the user explicitly asks.
- Avoid adding decorative fonts to a starter project unless the user requests a design direction.

## Sizing Rules

- Newly added visible text must stay at `20rpx` or above.
- Icon size is not text size, but default icon sizes should be `20rpx` or above for tap targets and readability.
- Keep interactive icon-only buttons large enough for touch by adding padding or a fixed hit area.

## Existing Code Boundary

- Do not replace an existing stable icon setup unless the user asks for that change.
- Do not migrate existing font utilities or icon classes proactively.
- Apply these rules to new functionality or user-requested edits only.
