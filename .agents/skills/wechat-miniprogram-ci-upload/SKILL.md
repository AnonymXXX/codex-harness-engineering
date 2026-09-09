---
name: wechat-miniprogram-ci-upload
description: >-
  Open, name, test, preview, and upload WeChat Mini Program builds with WeChat
  DevTools CLI preferred, including
  prompts such as 上传体验版, 上传开发版, 用 miniprogram-ci 上传, 生成小程序预览二维码,
  打开微信开发者工具, 项目名称/projectname, 代码上传密钥/private key/ci机器人,
  dev/build产物选择, 上传版本管理, or uploading uni-app mp-weixin output after
  build. Prefer WeChat DevTools CLI when installed and logged in; fall back to
  miniprogram-ci only when DevTools CLI is unavailable or the user explicitly
  requests key-based CI upload. Synchronize build-upload versions; keep Git
  publication separately authorized. Complete experience-version selection through
  the public platform only when requested; dev upload and preview do not change
  versions or tags.
---

# WeChat Mini Program CI Upload

## Tool Priority

1. **Primary: WeChat DevTools CLI**
   - Default path (macOS): `/Applications/wechatwebdevtools.app/Contents/MacOS/cli`
   - Requires WeChat DevTools installed, account logged in, and CLI/local service/automation available.
   - The CLI may start or reuse the DevTools local service; the IDE window may or may not open visibly.
2. **Fallback: `miniprogram-ci`**
   - Use only when:
     - DevTools CLI binary is missing under `/Applications`, or
     - DevTools CLI fails because it is not logged in / service port is unavailable / automation is disabled, or
     - The user explicitly asks for `miniprogram-ci` / 代码上传密钥 / CI robot upload.
   - Requires a usable private key from the user-provided path or project `.tmp`.
3. Do not silently switch tools. When falling back, tell the user the exact reason.

## DevTools GUI And Project Naming

- Use a meaningful mode-specific display name instead of generic names such as `src`
  or `mp-weixin`: `<业务名>-build` for build output and `<业务名>-dev` for dev output.
  Reuse an established project name when the repository already defines one.
- For uni-app, set the source `project.config.json#projectname` to the plain display
  name and `project.private.config.json#projectname` to the same value encoded with
  JavaScript `encodeURIComponent`. Rebuild and verify both generated output configs;
  do not patch generated configs as the durable fix.
- When the user asks to visibly open or test the project, inspect the DevTools main
  process. If it is running only as `Electron --cli`, close that instance normally,
  launch `/Applications/wechatwebdevtools.app` as a visible GUI, then run `cli open
  --project <output-dir>` against the validated output path.
- Verify the visible window title and the project-list card use the expected display
  name. A successful `cli open` is insufficient. If the card remains stale, use the
  DevTools Manage/remove-and-import flow; never edit DevTools internal cache.

### Cold-start AppID Binding Recheck

- A correct window title or project name does **not** prove that DevTools has bound
  the project to the expected AppID. DevTools can reuse a cached tourist/test
  registration for the same path after a cold start.
- If the IDE console or CLI reports `41002 appid missing`, `appid missing`,
  `测试号不支持上传`, or shows a test/tourist project, stop all upload/preview
  and Git finalization actions. Do not fall back to `miniprogram-ci` just because
  the project name is correct.
- Close the unbound project, then use DevTools **Manage/导入** to remove the stale
  registration and import the freshly generated `mp-weixin` output. Enter the
  expected AppID during import and confirm the project is a non-tourist project
  (`isTourist = false` when that field is available).
- Reopen the visible GUI and recheck all of: window title, project-list card,
  AppID, and a clean compile/run console. Only after the cold-start check is clean
  may `cli upload` or `cli preview` be retried. `cli open` success alone remains
  insufficient evidence of binding.

## Boundaries

- Both tools upload a WeChat Mini Program **development version** (开发版).
- CLI upload success alone does not establish experience-version selection (体验版).
- If the user says `上传体验版`, complete development-version upload and then [Experience-Version Selection](#experience-version-selection). A development-version upload or preview-only request ends after that requested result; do not add public-platform operations or login steps.
- The upload private key is only needed for `miniprogram-ci`. Do not guess, generate, search broad filesystem locations for, commit, or print private key contents.
- Build upload synchronizes version files and follows the global rules for local commits. Upload authorization does not grant Git tag, branch push, production, or MR/PR permissions. Resolve any separately authorized Git publication before uploading; missing optional Git publication authority does not block upload. Dev upload and preview QR generation do not edit versions, commit, tag, or push as part of this skill.

## Required Workflow

1. Confirm the repository has a WeChat Mini Program target.
   - For uni-app projects, prefer `mp-weixin` output.
   - Read `package.json`, `src/manifest.json`, and existing output `project.config.json` when present.
2. Resolve the output mode before upload or preview.
   - Use `build` mode by default.
   - Use `dev` mode when the user explicitly says `dev`, `开发产物`, `dist/dev`, or asks to upload/preview the dev output.
   - Use `build` mode when the user explicitly says `build`, `生产构建`, `dist/build`, or asks to upload/preview the build output.
   - Resolve the upload-description suffix from the output mode: `build` -> `（RELEASE）`; `dev` -> `（UAT）`. Do not infer it from the Git branch.
   - Report the resolved mode in the final result.
3. For build upload requests, resolve source ownership, version, and any Git publication scope before building.
   - In a Git repository, inspect the current branch, `git status --short`, and staged/unstaged diffs. Git and an `origin` remote are not prerequisites for uploading a valid project; require the relevant Git state only for authorized Git operations.
   - Attribute business-file changes. Validate and commit current-task changes under the existing global authorization with `$git-auto-commit`; do not ask the user to repeat an already authorized commit request. Preserve unrelated changes and isolate the upload source when they would otherwise be included. Ask only when source ownership, required dependencies, or the intended upload content cannot be determined safely.
   - Upload-managed version files are `package.json`, `manifest.json`, and `src/manifest.json`.
   - Resolve the upload version using the Version Management section, then synchronize only the intended version fields before building. Preserve unrelated changes in those files too.
   - Identify separately authorized branch/tag publication, its exact target, and side effects under the global Git workflow. If no publication is authorized, complete the upload without adding a Git publication approval step. If Git publication is required by the user but its scope is missing, prepare the concrete Git result and ask only about that operation while continuing the independently authorized upload.
   - Check tag availability only when tag creation is separately authorized. A tag conflict blocks tag publication, not an independently authorized upload; never overwrite a tag or silently change the requested version.
   - Skip this step for dev upload and all preview requests.
4. Always generate the latest mini-program output for the resolved mode before upload or preview.
   - In `build` mode, prefer `pnpm build:mp-weixin`; default output is `dist/build/mp-weixin`.
   - In `dev` mode, prefer `pnpm dev:mp-weixin` or the closest `uni -p mp-weixin` / `pnpm run dev` script; default output is `dist/dev/mp-weixin`.
   - If no exact script exists, inspect package scripts and choose the closest WeChat mini-program script for the requested mode.
   - If no script matches the requested mode, stop and explain which mode and script are missing.
   - For long-running dev/watch builds, wait until `app.json` and `project.config.json` exist and the target pages are present, then stop the watch process before upload when practical.
   - Stop if the build fails; do not upload stale output.
5. Use the freshly generated output directory for the resolved mode.
   - Build mode output: `dist/build/mp-weixin`.
   - Dev mode output: `dist/dev/mp-weixin`.
   - Verify it exists and contains `project.config.json` and `app.json` (or equivalent mini-program root files) before continuing.
   - Treat the output's generated `project.config.json` as authoritative for that output root. Never replace it with a repository-root or source-tree `project.config.json`.
6. Resolve AppID.
   - Prefer the built output `project.config.json`.
   - Fall back to `src/manifest.json` or user-provided AppID.
   - Record this value as the expected AppID. Stop if the available sources disagree, or if the resolved value is empty, `touristappid`, or another test/placeholder value.
7. Resolve command version and upload description.
   - For build upload, use the synchronized version from step 3.
   - For dev upload, use read-only version resolution: user-provided version, then `src/manifest.json` or `manifest.json` `versionName`, then `package.json` version. Do not edit files for dev upload.
   - For preview, use the same read-only version resolution as dev upload.
   - If the user only asks to generate a preview QR code and the purpose is unclear, use `验证小程序当前构建效果` as `<变更目的>`, then apply the Upload Description Policy suffix for the resolved mode.
   - Default robot is `1` only when using `miniprogram-ci`; DevTools CLI does not use robot.
8. Prefer WeChat DevTools CLI for upload/preview.
   - Resolve CLI path (see WeChat DevTools CLI section).
   - Use the freshly generated `dist/build/mp-weixin` directly by default. A completed build output is already stable.
   - For dev mode, stop the watcher when practical and use the completed `dist/dev/mp-weixin` directly.
   - Prepare `<repo>/.tmp/upload-mp-weixin/` only when the resolved output is still volatile or a stable copy is otherwise necessary:
     - Recreate only that exact task-owned temporary directory before copying; do not merge a fresh build into stale files.
     - Copy the complete generated output, including its own `project.config.json`.
     - Never overlay that file with a repository-root or source-tree project config.
     - When the copied directory itself is the mini-program root, `miniprogramRoot` and `srcMiniprogramRoot` must be absent or `"./"`. Reject a copied config that still points to `dist/build/mp-weixin/`, `dist/dev/mp-weixin/`, or another nested source path.
   - Optionally `cli open --project <path>` before `upload`/`preview` if the first compile attempt fails with missing `app.json`.
   - Treat a successful `cli open` only as confirmation that the IDE accepted the path; it does not prove that the project is bound to the expected AppID.
   - Run upload or preview with DevTools CLI.
   - Apply the DevTools AppID Binding Guardrail before treating the command as successful.
9. Fall back to `miniprogram-ci` only when step 8 cannot proceed.
   - Explain the fallback reason to the user first.
   - Do not treat `41002 appid missing`, `测试号不支持上传`, or an AppID mismatch as a generic CLI availability failure. Resolve the DevTools project binding or stop; do not fall back solely because of one of these errors.
   - Resolve private key path:
     - User-provided path, or
     - project-local `.tmp/private.<appid>.key`, or
     - project-local `.tmp/private.key`.
   - Verify the key file exists, but never display its contents.
   - Do not search broad filesystem locations such as `~/Downloads` unless the user provided the path.
   - If no usable key exists, stop and report that DevTools CLI failed/unavailable and no key is available for `miniprogram-ci`.
   - Prepare `.tmp/miniprogram-ci-work/` and run `miniprogram-ci` from that directory with absolute paths.
10. Clean up temporary artifacts after the command finishes.
    - For DevTools path: leave `.tmp/upload-mp-weixin/` in place unless the user asks to clean it.
    - For `miniprogram-ci`: remove empty `.tmp/miniprogram-ci-work/[0-9a-f]{32}` directories automatically; leave non-empty ones and report the path.
11. After build upload succeeds, follow [Build Upload Git Finalization](#build-upload-git-finalization). Keep upload success separate from any blocked or failed Git operation. Skip this step for dev upload and all preview requests.
12. If the user requested an experience version, complete [Experience-Version Selection](#experience-version-selection) after a successful upload, independently of optional Git publication. Otherwise finish at the requested development-version upload or preview.
13. Report command outcome, output mode (`dev` or `build`), output directory, tool, AppID, version, robot when applicable, description, and Git status for build uploads. Distinguish development-version upload, experience-version selection, and preview QR. For dev upload, report that this skill skipped version sync and tag/push. If experience selection is blocked, report `开发版上传成功；体验版选择尚未完成` with the concrete blocker; do not describe the whole experience-version request as complete.

## Experience-Version Selection

Use this section only when the user explicitly requests an experience version for the uploaded project. That request covers selecting the uploaded development version as the experience version, not submitting it for review, publishing production, or changing members or tester permissions.

1. After successful upload with the expected AppID, use the current `$ego-browser` skill and an independent Task Space to inspect the WeChat public platform. Follow current visible navigation rather than assuming fixed selectors.
2. Verify the account/project AppID and identify the uploaded development version using its version, description, upload time, and other available evidence. Do not select a different or ambiguous record. Reuse a signed-in session; if login, QR verification, CAPTCHA, or a browser-owned approval requires the user, hand off under the global human-verification rules and resume only after the user confirms.
3. Select that record as the experience version within the authorized scope. Read the resulting platform state to verify the selected version. Keep any experience QR or result page available only when needed by the user, following the current browser completion policy.
4. If access, account scope, or available platform controls prevent selection, report the completed upload and remaining selection step. Continue independent authorized work; do not bypass access controls or substitute a production-release action.

## DevTools AppID Binding Guardrail

Apply this guardrail to every DevTools CLI upload or preview:

1. Compare the user-requested AppID when present, the expected AppID resolved from project files, and the AppID reported by the CLI. All available values must match exactly.
2. For upload, require the CLI output to report the expected AppID, such as `使用 AppID: <expected-appid>`, before accepting `upload` success.
3. Stop immediately when the IDE or CLI shows `41002 appid missing`, `appid missing`, `测试号不支持上传`, a test/tourist project, or any AppID mismatch. Do not upload, commit version files, create a tag, or push.
4. Do not edit WeChat DevTools internal cache or local-storage files to manufacture a binding. Reopening the same path after changing `project.config.json` may reuse an earlier unbound/test-project cache entry and is not a valid fix.
5. If a new path was cached as unbound, close it. Prefer the DevTools
   Manage/导入 flow to remove the stale registration and import the exact
   validated output with the expected AppID; confirm `isTourist = false` when
   available. Rebuilding or reopening the same path without re-importing does
   not repair the binding.
6. Re-run the visible GUI cold-start check and then the CLI command after
   correcting the binding. Accept success only after the expected AppID is
   reported and no `appid missing` error remains.

## Upload Description Policy

Preserve the base remark format and append exactly one full-width suffix based only on the resolved output mode:

| Output mode | Suffix |
| --- | --- |
| `build` | `（RELEASE）` |
| `dev` | `（UAT）` |

```text
release v<版本号> <变更目的><模式后缀>
```

Examples:

```text
build: release v1.0.0 更新小程序开发版本（RELEASE）
dev:   release v1.0.0 验证账单解析与预算统计流程（UAT）
```

Rules:

- Resolve the output mode before creating any upload description, using the mode rules in the Required Workflow section.
- Map `build` to `（RELEASE）` and `dev` to `（UAT）`; use this mapping for every upload and preview description.
- Append exactly one suffix at the end. Never omit it, use half-width parentheses, or append both `（UAT）` and `（RELEASE）`.
- In command templates, replace `<模式后缀>` with the literal suffix for the resolved mode; never upload the placeholder unchanged.
- Infer `<变更目的>` from the user's request, recent task context, README, page names, or recent commit subjects when it is clear.
- If the purpose is unclear, use:

```text
build: release v<版本号> 更新小程序开发版本（RELEASE）
dev:   release v<版本号> 更新小程序开发版本（UAT）
```

- Do not include commit hashes in the upload description by default; report them separately if useful.
- Avoid vague or tool-noisy descriptions such as `体验版`, `test`, `upload`, or `miniprogram-ci 体验版 ff373be`.

## Version Management

Apply this section only to build upload requests. Dev upload and preview QR requests must resolve a version read-only and must not edit, commit, tag, or push version files.

Upload version resolution:

- If the user provides an explicit SemVer version, use it.
- Otherwise read `versionName` from `src/manifest.json` or `manifest.json`.
- If manifest `versionName` is missing, read `package.json` `version`.
- Treat missing values, empty values, and `0.0.0` as placeholders.
- If both package and manifest versions exist but differ, prefer manifest `versionName` for uni-app mini-program uploads.
- If no usable version exists, start from `1.0.0`.

Upload version bump:

- If the user explicitly provides a final version, do not bump it.
- If the user explicitly says `major`, `minor`, or `patch`, apply that SemVer bump.
- Otherwise infer the bump from the user request, current `git diff`, staged diff, and recent commit subjects using the same change-type spirit as `$git-auto-commit`:
  - New features, new pages, or substantial user-facing capability: `minor`.
  - Fixes, style changes, copy changes, API adaptation, small UI adjustments, or local optimizations: `patch`.
  - `major` only when the user explicitly asks for it or the change is clearly breaking.
- When inference is uncertain, default to `patch` and report that default in the final result.

Synchronize version files before building:

- Set `package.json` `version` to the resolved upload version when `package.json` exists.
- Set `manifest.json` or `src/manifest.json` `versionName` to the same version when present.
- Set manifest `versionCode` to the SemVer digits without dots, such as `1.0.0 -> 100`, `1.2.3 -> 123`, and `1.10.3 -> 1103`.
- Use structured JSON parsing/editing when possible; preserve unrelated fields.
- Do not update version files for dev upload or preview-only requests.

Before a build upload with separately authorized tag creation, check tag availability for that Git publication:

```bash
git rev-parse -q --verify refs/tags/v<version>
git ls-remote --tags origin v<version>
```

If either local or remote tag already exists, stop tag creation and report the conflict. Do not overwrite, delete, or auto-bump after a tag conflict. This Git conflict does not block an independently authorized upload of the resolved version.

## Build Upload Git Finalization

Run this section only after a build upload command succeeds in a Git repository. Do not run it for dev upload, preview QR generation, or any failed upload. Git publication is optional unless the user's request separately requires it.

Rules:

- Stage only attributable version changes in `package.json`, `manifest.json`, and `src/manifest.json`; never stage unrelated fields or business changes wholesale. Follow the global local-commit rules and task-history safeguards. Business commits use `$git-auto-commit` within their existing authorization and need no repeated request.
- If no version fields changed, skip the version commit. A no-op version commit does not create tag or push authority.
- Commit message must be exactly:

```text
chore: release v<version>
```

- Only with explicit authorization for the exact tag, create a lightweight tag on the verified commit representing the uploaded source and version. Recheck for source drift and local/remote tag conflicts first:

```bash
git tag v<version> <verified-upload-commit>
```

- Execute only separately authorized Git publication. Use the global Git workflow's validation and integration preflight for the exact authorized branch target; never choose a publication target solely because it is the current branch. Tag publication requires explicit authorization and a verified tag target. Commands for the independently authorized operations are:

```bash
# Only when branch publication is authorized and preflight permits it:
git push origin <validated-task-ref>:refs/heads/<authorized-target>
# Only when this exact tag publication is explicitly authorized:
git push origin refs/tags/v<version>:refs/tags/v<version>
```

- Without Git publication authority, finish the upload and eligible local commit, then report `Git 发布：未执行（未授权）`; do not ask for an optional publication. If an authorized Git operation fails, preserve the successful upload and report the exact Git blocker separately.
- Do not commit generated mini-program output unless it is required by the authorized task or project rules.

## Command Templates

In every command below, `<absolute-mp-weixin-output-dir>` is the freshly generated output for the resolved mode. Use a stable copy only under the step 8 conditions:

```text
build -> <repo>/dist/build/mp-weixin
dev   -> <repo>/dist/dev/mp-weixin
stable copy (only when needed) -> <repo>/.tmp/upload-mp-weixin
```

### Primary: WeChat DevTools CLI

Default macOS CLI path:

```text
/Applications/wechatwebdevtools.app/Contents/MacOS/cli
```

If that path is missing, try to locate `wechatwebdevtools.app` under `/Applications` only. Do not perform broad filesystem searches.

Upload a build-mode development version:

```bash
/Applications/wechatwebdevtools.app/Contents/MacOS/cli upload \
  --project <absolute-mp-weixin-output-dir> \
  --version <version> \
  --desc "release v<版本号> <变更目的>（RELEASE）" \
  --lang zh
```

Upload a dev-mode development version:

```bash
/Applications/wechatwebdevtools.app/Contents/MacOS/cli upload \
  --project <absolute-mp-weixin-output-dir> \
  --version <version> \
  --desc "release v<版本号> <变更目的>（UAT）" \
  --lang zh
```

Generate a preview QR code:

```bash
/Applications/wechatwebdevtools.app/Contents/MacOS/cli preview \
  --project <absolute-mp-weixin-output-dir> \
  --qr-format image \
  --qr-output <absolute-preview-image-path> \
  --lang zh
```

Preview output should default to `.tmp/miniprogram-ci-preview.png` unless the user specifies another path. The DevTools CLI preview command has no description flag; any recorded preview description still follows `build` -> `（RELEASE）` and `dev` -> `（UAT）`.

Stable-copy prep when the generated output cannot be used directly:

```bash
# if this exact task-owned directory exists, move it to Trash before recreating it
mkdir -p <repo>/.tmp/upload-mp-weixin
cp -R <absolute-mp-weixin-output-dir>/. <repo>/.tmp/upload-mp-weixin/
# keep the generated project.config.json; never overlay a repository-root config
# require miniprogramRoot/srcMiniprogramRoot to be absent or "./"
```

If CLI reports `app.json is not found in the project root directory`:

1. Confirm `app.json` exists in the project root used for `--project`.
2. Stop a live watcher or prepare `.tmp/upload-mp-weixin` under the stable-copy rules above.
3. Run `cli open --project <path>` once, then retry upload.
4. Only then consider `miniprogram-ci` fallback if a key is available.

If the CLI reports that the account is not logged in, the service port is unavailable, or automation is not enabled, either fall back to `miniprogram-ci` when a key exists, or stop and tell the user the specific missing condition.

### Fallback: miniprogram-ci

Use only under the Tool Priority fallback conditions.

Upload a build-mode development version:

```bash
cd <repo>/.tmp/miniprogram-ci-work && pnpm dlx miniprogram-ci upload \
  --appid <appid> \
  --project-path <absolute-mp-weixin-output-dir> \
  --private-key-path <private-key-path> \
  --upload-version <version> \
  --upload-description "release v<版本号> <变更目的>（RELEASE）" \
  --robot <robot> \
  --use-project-config \
  --locales zh
```

Upload a dev-mode development version:

```bash
cd <repo>/.tmp/miniprogram-ci-work && pnpm dlx miniprogram-ci upload \
  --appid <appid> \
  --project-path <absolute-mp-weixin-output-dir> \
  --private-key-path <private-key-path> \
  --upload-version <version> \
  --upload-description "release v<版本号> <变更目的>（UAT）" \
  --robot <robot> \
  --use-project-config \
  --locales zh
```

Generate a build-mode preview QR code:

```bash
cd <repo>/.tmp/miniprogram-ci-work && pnpm dlx miniprogram-ci preview \
  --appid <appid> \
  --project-path <absolute-mp-weixin-output-dir> \
  --private-key-path <absolute-private-key-path> \
  --upload-version <version> \
  --upload-description "release v<版本号> <变更目的>（RELEASE）" \
  --robot <robot> \
  --use-project-config \
  --enable-qrcode \
  --qrcode-format image \
  --qrcode-output-dest <absolute-preview-image-path> \
  --locales zh
```

Generate a dev-mode preview QR code:

```bash
cd <repo>/.tmp/miniprogram-ci-work && pnpm dlx miniprogram-ci preview \
  --appid <appid> \
  --project-path <absolute-mp-weixin-output-dir> \
  --private-key-path <absolute-private-key-path> \
  --upload-version <version> \
  --upload-description "release v<版本号> <变更目的>（UAT）" \
  --robot <robot> \
  --use-project-config \
  --enable-qrcode \
  --qrcode-format image \
  --qrcode-output-dest <absolute-preview-image-path> \
  --locales zh
```

For a plain `生成预览二维码` request, use this default description unless task context provides a clearer purpose:

```text
build: release v<版本号> 验证小程序当前构建效果（RELEASE）
dev:   release v<版本号> 验证小程序当前构建效果（UAT）
```

## Safety Notes

- Prefer WeChat DevTools CLI; do not require a private key for the default path.
- Do not add upload private keys to Git.
- Do not echo private key contents into logs.
- Do not upload when the latest build failed.
- Do not accept `cli open` success as AppID validation.
- Do not upload, commit, tag, or push after `41002 appid missing`, `测试号不支持上传`, a tourist/test project, or an AppID mismatch.
- Do not overwrite a generated output `project.config.json` with a config from another directory level.
- Do not edit WeChat DevTools internal cache or local-storage files to force an AppID binding.
- Public-platform access is limited to explicitly requested experience-version selection. Preserve login/CAPTCHA handoff and separate production, review-submission, and permission-change authorization.
- Do not run `miniprogram-ci` from the repository root when avoidable, because it may create 32-character hash temporary directories in the current working directory.
- Do not fall back to `miniprogram-ci` silently; always state the DevTools failure or user request reason first.
- Do not tag before build upload succeeds or without explicit tag authorization.
- Do not tag or push for dev upload or preview-only requests.
- Do not modify version files for dev upload or preview-only requests.
- Do not overwrite existing local or remote tags.
