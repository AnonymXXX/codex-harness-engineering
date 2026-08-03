# Harness Engineering Recovery

## Purpose

Restore global Codex rules, custom agents, Harness workflows, and selected user-managed skills on
a new macOS machine without copying credentials, sessions, memory, caches, or machine-specific
Codex configuration into Git.

## Distribution Model

- `core` installs global Harness rules, the `luna_worker` custom agent, and five core engineering skills.
- `daily` extends `core` with frequently used portable skills.
- A private overlay can be loaded from a separately cloned local repository by explicitly supplying
  its source path and profile. The public distribution does not discover, catalog, or clone overlays.
- Managed files are symlinked into `~/.codex` and `~/.agents/skills` so Git remains the versioned
  source of truth.
- Codex-managed system skills remain owned by Codex and are not copied into this repository.

## Recovery Contract

The installer provides these public commands:

```text
python3 scripts/harness_setup.py install --profile core|daily [--overlay-source <path> --overlay-profile <name>]
python3 scripts/harness_setup.py check --profile core|daily [--overlay-source <path> --overlay-profile <name>]
python3 scripts/harness_setup.py credentials set <service> --overlay-source <path>
python3 scripts/harness_setup.py docs --check
```

`--overlay-source` and `--overlay-profile` must be provided together for `install` and `check`.
The source must already exist and contain a version 1 `profiles.json`; the installer never clones it.

`install` supports `--dry-run` and a test-only `--home <path>`. It is idempotent. A conflicting
destination is preserved under a timestamped backup directory before a symlink is created. The
installer never copies, links, creates, or automatically overwrites the machine-specific
`~/.codex/config.toml`, credentials, sessions, memory, or caches.

During an upgrade, `install` also retires a stale public-distribution skill symlink when its name is
absent from the current manifest and it still points directly to the same-name skill path in this
distribution. Directories, ordinary files, links to another repository, and active skills are preserved.

After installation, the command runs or reports the Skill index check, Harness Doctor,
documentation consistency, security scan, and selected-profile dependency checks. A normal
installation against the current HOME refreshes the index and runs Doctor. An explicit `--home`
rehearsal skips those two global checks.

## Credential Contract

- Real credentials never enter this repository.
- An overlay may declare Keychain service metadata in its own local manifest.
- Passwords are entered through macOS Keychain's secure prompt, never passed as command-line
  arguments, printed, or retained in normal backup directories.
- Runtime scripts may prefer an explicit environment variable before Keychain when their private
  manifest declares that behavior.
- Browser preferences use a tracked template and an ignored local `config.env`.

## New Mac Procedure

Prerequisites are Codex CLI, Git, Python 3, and GitHub CLI.

```bash
gh repo clone AnonymXXX/codex-harness-engineering ~/.local/share/codex-harness-engineering
python3 ~/.local/share/codex-harness-engineering/scripts/harness_setup.py install --profile daily
python3 ~/.local/share/codex-harness-engineering/scripts/harness_setup.py check --profile daily
```

For an optional private overlay, clone it separately and rerun `install` and `check` with its
absolute `--overlay-source` path and `--overlay-profile` name.

The official `[agents].max_concurrent_threads_per_session` setting is the maximum number of
concurrent agent threads outside the main Codex thread. On a new machine, merge the following
section into the machine-specific `~/.codex/config.toml` while preserving unrelated settings:

```toml
[agents]
enabled = true
max_concurrent_threads_per_session = 5
```

The installer must not create, copy, link, or automatically overwrite this file. Codex reads the
setting only when a new task starts. Start a new Codex task after installation.

## Update And Rollback

Update each cloned repository with `git pull --ff-only`, rerun the same `install` command, then run
`check`. Do not replace local divergent work automatically.

If installation preserves a conflict, it reports the exact backup path. To roll back, remove only
the newly created symlink with `/usr/bin/trash` and move the preserved entry back to its original
path. Permanent deletion is not part of recovery or rollback.

## Acceptance Criteria

- `core` and `daily` resolve deterministically from the public `profiles.json`.
- An explicit external overlay resolves only from its own Manifest and selected Profile.
- A temporary empty HOME can install and check profiles twice without drift.
- The installed `luna_worker` matches the tracked TOML and is available to fresh Codex tasks.
- The tracked public Skill inventory matches the Manifest and actual directories.
- Security checks reject real environment files, Codex config, private keys, nested Git metadata,
  generated caches, known credential formats, and hardcoded database passwords.
- Harness tests, Skill index checks, Doctor, and a fresh Codex discovery smoke test pass.
