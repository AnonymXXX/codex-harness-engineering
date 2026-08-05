# Harness Engineering Recovery

## Purpose

Restore global Codex rules, custom agents, Harness workflows, and selected user-managed skills on
a new macOS machine without copying credentials, sessions, memory, caches, or machine-specific
Codex configuration into Git.

## Distribution Model

- `core` installs global Harness rules, the `deepseek_v4_flash_worker` custom agent, and five core
  engineering skills.
- `daily` extends `core` with frequently used portable skills.
- A private overlay can be loaded from a separately cloned local repository by explicitly supplying
  its source path and profile. The public distribution does not discover, catalog, or clone overlays.
- Managed files are symlinked into `~/.codex` and `~/.agents/skills` so Git remains the versioned
  source of truth.
- Codex-managed system skills remain owned by Codex and are not copied into this repository.
- Flash dispatches use the tracked route marker, seven-field task contract, and structured response contract.
  The seven fields are `Objective`, `Ownership`, `Starting State`, `Interfaces`, `Constraints`, `Git Boundary`,
  and `Verification`; the detailed lifecycle remains in the Harness workflow. Cross-provider spawns use
  `fork_turns = "1"` and carry the complete seven-field task in the parent context immediately before the call.
- Worker write paths stay exclusively owned until the main agent records release. An ordinary quality defect
  uses one same-Worker `followup_task` marked `Correction: 1/1`; unrelated work gets a new spawn.
  A root task reports adopted, partially adopted, rejected, and failed Flash work-unit counts so Harness
  Doctor can audit actual result use and route compliance.
- Every completed root turn that used a named Worker appends the exact final marker `Worker 协议：version=10`.
  A same-Worker correction or invalid reuse also appends `Worker 纠错：started=<n> completed=<n> failed=<n> violations=<n>`;
  `started + violations` counts associated followup turns and `completed + failed = started`. Followup messages may be encrypted,
  so Doctor reconciles the unencrypted final marker. Roots without v10 remain
  historical/informational.
- A root using `deepseek_v4_flash_worker` emits exactly one `Flash 验收：adopted=<n> partial=<n> rejected=<n> failed=<n>`
  line after review. Worker caps are enforced per root session (8 total); aggregate/global peaks are informational.
  When practical, split units expected beyond 30 minutes; this is advisory, not a timeout or ordinary
  interruption reason.
- Harness Doctor continues to parse the old v9 Luna/Terra protocol as historical compatibility data, but
  new dispatches use only `deepseek_v4_flash_worker`.

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
concurrent agent threads outside the main Codex thread. The total spawned-thread limit is `8` for this
setup. On a new machine, merge the following section into the machine-specific `~/.codex/config.toml`
while preserving unrelated settings:

```toml
[agents]
enabled = true
max_concurrent_threads_per_session = 8
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
- The installed `deepseek_v4_flash_worker` matches its tracked TOML file and is available to fresh Codex tasks.
- A fresh task can dispatch Flash with the seven-field structured contract and emits the exact
  `Worker 协议：version=10` marker for every completed root turn that used a named Worker. When correction
  or invalid reuse occurs, it also emits the exact `Worker 纠错：started=<n> completed=<n> failed=<n> violations=<n>`
  marker. Conditional reports remain required: a direct Worker interruption emits the exact interruption
  line below once, and a completed root turn using Flash emits exactly one machine-readable acceptance line
  after review.
- When a direct Worker turn is interrupted, the root task emits this exact line with only the five approved reasons:

  ```text
  Worker 中断：overlap=<n> unsafe=<n> scope_violation=<n> user_redirect=<n> unresponsive=<n>
  ```
- The tracked public Skill inventory matches the Manifest and actual directories.
- Security checks reject real environment files, Codex config, private keys, nested Git metadata,
  generated caches, known credential formats, and hardcoded database passwords.
- Harness tests, Skill index checks, Doctor, and a fresh Codex discovery smoke test pass.
