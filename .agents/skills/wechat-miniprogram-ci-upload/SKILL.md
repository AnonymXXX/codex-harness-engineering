---
name: wechat-miniprogram-ci-upload
description: >-
  Upload WeChat Mini Program builds with WeChat DevTools CLI preferred, including
  prompts such as 上传体验版, 上传开发版, 用 miniprogram-ci 上传, 生成小程序预览二维码,
  代码上传密钥/private key/ci机器人, dev/build产物选择, 上传版本管理, or uploading
  uni-app mp-weixin output after build. Prefer WeChat DevTools CLI when installed
  and logged in; fall back to miniprogram-ci only when DevTools CLI is unavailable
  or the user explicitly requests key-based CI upload. Build upload success should
  synchronize mini-program version files, commit chore release version, tag the
  version, and push the branch plus tag; dev upload and preview do not change
  versions or tags.
---

# WeChat Mini Program CI Upload

## Worker Routing

Follow the shared dispatch, concurrency, safety, and review rules in `~/.codex/docs/workflows/harness-engineering.md`; this section maps only this skill's preflight and delivery phases.

- Prefer `luna_worker` with `Route: wechat-miniprogram-ci-upload/preflight` only for local read-only inspection of project configuration, version state, artifact paths, and existing build evidence.
- Keep builds with mutable outputs, uploads, version synchronization, commits, tags, pushes, credential handling, and final delivery verification with the main agent.

Use this skill for WeChat Mini Program upload and preview flows. **Prefer WeChat DevTools CLI** for upload and preview. Use `miniprogram-ci` only as a fallback when DevTools CLI is unavailable, not logged in, or the user explicitly asks for key-based CI upload.

This is a release/CI workflow. Do not mix it into app feature development rules.

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

## Boundaries

- Both tools upload a WeChat Mini Program **development version** (开发版).
- Official tooling does not automatically select that version as the experience version (体验版).
- If the user says `上传体验版`, interpret the executable step as uploading a development version only. Do not open, navigate, log in to, or operate the WeChat public platform to select an experience version; that manual selection remains the user's responsibility and is outside this skill.
- Do not ask the user to log in to the WeChat public platform or wait for login after an upload.
- The upload private key is only needed for `miniprogram-ci`. Do not guess, generate, search broad filesystem locations for, commit, or print private key contents.
- Build upload success creates a Git version commit, lightweight tag, and push. Dev upload and preview QR generation do not edit versions, commit, tag, or push.

## Required Workflow

1. Confirm the repository has a WeChat Mini Program target.
   - For uni-app projects, prefer `mp-weixin` output.
   - Read `package.json`, `src/manifest.json`, and existing output `project.config.json` when present.
2. Resolve the output mode before upload or preview.
   - Use `build` mode by default.
   - Use `dev` mode when the user explicitly says `dev`, `开发产物`, `dist/dev`, or asks to upload/preview the dev output.
   - Use `build` mode when the user explicitly says `build`, `生产构建`, `dist/build`, or asks to upload/preview the build output.
   - Report the resolved mode in the final result.
3. For build upload requests, run Git and version preflight before building.
   - Verify the repo is a Git repository, the current branch can be resolved, and `origin` exists.
   - Inspect `git status --short`. If files other than upload-managed version files are modified, stop and tell the user to commit business changes first with `$git-auto-commit`.
   - Upload-managed version files are `package.json`, `manifest.json`, and `src/manifest.json`.
   - Resolve the upload version using the Version Management section, then synchronize version files before building.
   - If local or remote tag `v<version>` already exists, stop and report the conflict before building or uploading.
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
6. Resolve AppID.
   - Prefer the built output `project.config.json`.
   - Fall back to `src/manifest.json` or user-provided AppID.
7. Resolve command version and upload description.
   - For build upload, use the synchronized version from step 3.
   - For dev upload, use read-only version resolution: user-provided version, then `src/manifest.json` or `manifest.json` `versionName`, then `package.json` version. Do not edit files for dev upload.
   - For preview, use the same read-only version resolution as dev upload.
   - If the user only asks to generate a preview QR code and the purpose is unclear, use `release v<版本号> 验证小程序当前构建效果`.
   - Default robot is `1` only when using `miniprogram-ci`; DevTools CLI does not use robot.
8. Prefer WeChat DevTools CLI for upload/preview.
   - Resolve CLI path (see WeChat DevTools CLI section).
   - Prepare a stable upload directory (recommended):
     - Copy the resolved `mp-weixin` output into `<repo>/.tmp/upload-mp-weixin/`.
     - Ensure `project.config.json` has `miniprogramRoot`/`srcMiniprogramRoot` of `"./"` when missing.
     - Upload from this stable copy instead of a live watch-output directory when possible.
   - Optionally `cli open --project <path>` before `upload`/`preview` if the first compile attempt fails with missing `app.json`.
   - Run upload or preview with DevTools CLI.
9. Fall back to `miniprogram-ci` only when step 8 cannot proceed.
   - Explain the fallback reason to the user first.
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
11. After build upload succeeds, commit and tag the synchronized version files.
    - Stage only upload-managed version files that changed.
    - Commit with exactly `chore: release v<version>`.
    - Create a lightweight tag named `v<version>`.
    - Push the current branch and tag with `git push origin <current-branch> v<version>`.
    - If commit, tag, or push fails, report the exact failure and do not hide that the upload itself already succeeded.
    - Skip this step for dev upload and all preview requests.
12. Report whether the command succeeded, the output mode (`dev` or `build`), output directory, tool used (`WeChat DevTools CLI` or `miniprogram-ci`), the AppID, version, robot when applicable, description, tag/push status for build uploads, and whether the result is a development version or preview QR. For dev upload, explicitly report that version sync and tag/push were skipped because `dev` mode is for development validation. State that the uploaded result is a development version and stop; do not offer or attempt experience-version selection.

## Upload Description Policy

Use a formal, meaningful project remark:

```text
release v<版本号> <变更目的>
```

Examples:

```text
release v1.0.0 验证账单解析与预算统计流程
release v1.0.0 更新小程序开发版本
```

Rules:

- Infer `<变更目的>` from the user's request, recent task context, README, page names, or recent commit subjects when it is clear.
- If the purpose is unclear, use:

```text
release v<版本号> 更新小程序开发版本
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

Before build upload, check tag availability:

```bash
git rev-parse -q --verify refs/tags/v<version>
git ls-remote --tags origin v<version>
```

If either local or remote tag already exists, stop and report the conflict. Do not overwrite, delete, or auto-bump after a tag conflict.

## Build Upload Git Finalization

Run this section only after a build upload command succeeds. Do not run it for dev upload, preview QR generation, or any failed upload.

Rules:

- Stage only changed upload-managed version files: `package.json`, `manifest.json`, and `src/manifest.json`.
- If no version files changed, skip the version commit but still create and push the tag when it does not already exist.
- Commit message must be exactly:

```text
chore: release v<version>
```

- Create a lightweight tag:

```bash
git tag v<version>
```

- Push the current branch and tag:

```bash
git push origin <current-branch> v<version>
```

- If tag creation or push fails after upload has succeeded, report the upload success separately from the Git finalization failure.
- Do not commit business files or generated mini-program output unless the user explicitly requests a separate commit flow; route business commits to `$git-auto-commit`.

## Command Templates

In every command below, `<absolute-mp-weixin-output-dir>` is the freshly generated output for the resolved mode, or preferably a stable copy at `<repo>/.tmp/upload-mp-weixin`:

```text
build -> <repo>/dist/build/mp-weixin
dev   -> <repo>/dist/dev/mp-weixin
stable copy (recommended) -> <repo>/.tmp/upload-mp-weixin
```

### Primary: WeChat DevTools CLI

Default macOS CLI path:

```text
/Applications/wechatwebdevtools.app/Contents/MacOS/cli
```

If that path is missing, try to locate `wechatwebdevtools.app` under `/Applications` only. Do not perform broad filesystem searches.

Upload a development version:

```bash
/Applications/wechatwebdevtools.app/Contents/MacOS/cli upload \
  --project <absolute-mp-weixin-output-dir> \
  --version <version> \
  --desc "release v<版本号> <变更目的>" \
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

Preview output should default to `.tmp/miniprogram-ci-preview.png` unless the user specifies another path.

Recommended stable-copy prep before CLI upload:

```bash
rm -rf <repo>/.tmp/upload-mp-weixin
mkdir -p <repo>/.tmp/upload-mp-weixin
cp -R <absolute-mp-weixin-output-dir>/. <repo>/.tmp/upload-mp-weixin/
# ensure miniprogramRoot is "./" in project.config.json when missing
```

If CLI reports `app.json is not found in the project root directory`:

1. Confirm `app.json` exists in the project root used for `--project`.
2. Prefer uploading from `.tmp/upload-mp-weixin` rather than a live watch output.
3. Run `cli open --project <path>` once, then retry upload.
4. Only then consider `miniprogram-ci` fallback if a key is available.

If the CLI reports that the account is not logged in, the service port is unavailable, or automation is not enabled, either fall back to `miniprogram-ci` when a key exists, or stop and tell the user the specific missing condition.

### Fallback: miniprogram-ci

Use only under the Tool Priority fallback conditions.

Upload a development version:

```bash
cd <repo>/.tmp/miniprogram-ci-work && pnpm dlx miniprogram-ci upload \
  --appid <appid> \
  --project-path <absolute-mp-weixin-output-dir> \
  --private-key-path <private-key-path> \
  --upload-version <version> \
  --upload-description "release v<版本号> <变更目的>" \
  --robot <robot> \
  --use-project-config \
  --locales zh
```

Generate a preview QR code:

```bash
cd <repo>/.tmp/miniprogram-ci-work && pnpm dlx miniprogram-ci preview \
  --appid <appid> \
  --project-path <absolute-mp-weixin-output-dir> \
  --private-key-path <absolute-private-key-path> \
  --upload-version <version> \
  --upload-description "release v<版本号> <变更目的>" \
  --robot <robot> \
  --use-project-config \
  --enable-qrcode \
  --qrcode-format image \
  --qrcode-output-dest <absolute-preview-image-path> \
  --locales zh
```

For a plain `生成预览二维码` request, use this default description unless task context provides a clearer purpose:

```text
release v<版本号> 验证小程序当前构建效果
```

## Safety Notes

- Prefer WeChat DevTools CLI; do not require a private key for the default path.
- Do not add upload private keys to Git.
- Do not echo private key contents into logs.
- Do not upload when the latest build failed.
- Never access the WeChat public platform, request a platform login, or attempt to select the uploaded development version as the experience version.
- Do not run `miniprogram-ci` from the repository root when avoidable, because it may create 32-character hash temporary directories in the current working directory.
- Do not fall back to `miniprogram-ci` silently; always state the DevTools failure or user request reason first.
- Do not tag before build upload succeeds.
- Do not tag or push for dev upload or preview-only requests.
- Do not modify version files for dev upload or preview-only requests.
- Do not overwrite existing local or remote tags.
