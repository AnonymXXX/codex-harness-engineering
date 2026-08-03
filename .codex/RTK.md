# RTK Safe Usage For Codex

Use RTK only when its human-readable output is the final result consumed by
Codex. Correctness and recoverability take priority over token savings.

## Preferred Commands

Use RTK for read-only, human-readable inspection and noisy validation output:

```bash
rtk ls .
rtk read path/to/file
rtk rg "pattern" .
rtk find "*.go" .
rtk git status
rtk git log -n 10
rtk git diff
rtk cargo test
rtk pytest -q
rtk npm run build
rtk pnpm test
rtk lint
rtk tsc
```

On test, lint, typecheck, or build failure, use RTK's full-output/tee hint when
the compact result is insufficient. Do not rerun blindly.

## Mandatory Bypass

Use the native command, not RTK, in these cases:

- The output feeds another command through `|`, `xargs`, `while read`, command
  substitution, redirection, or another machine-processing step.
- Exact JSON, CSV, hashes, patches, byte counts, line counts, or other
  machine-readable output is required.
- Reading screenshots, images, base64, binary data, secrets, exact source text,
  or production incident evidence.
- Any linked Git worktree Git command. Use native `git` for status, diff, log,
  staging, commits, merging, and branch checks inside worktrees.
- State-changing Git commands: `git add`, `git commit`, `git push`, `git pull`,
  `git merge`, `git rebase`, `git tag`, and branch/worktree operations.
- Deployment, upload, release, migration, database, permission, or production
  operations.
- The user explicitly requests raw or complete output.

When uncertain, use the native command. `rtk proxy <cmd>` is allowed only when
tracking is useful and the command does not fall into a sensitive category.

## Analytics

```bash
rtk gain
rtk gain --history
rtk session
```

Codex also uses `~/.codex/hooks.json` with the local safety policy under
`~/.codex/rtk/`. In `observe` mode the hook records only hashes and decisions;
in `enforce` mode it rewrites only commands that pass the mandatory bypass
rules above.
