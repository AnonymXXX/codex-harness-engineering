# Codex Harness Engineering

[简体中文](README.md) | **English**

A versioned engineering workflow for Codex. It helps Codex choose an execution approach based on
task risk, route work to the appropriate skills, isolate medium- and high-risk changes when needed,
perform proportionate validation, and preserve only project knowledge that should remain durable.

You do not need to read every rule first. The recommended starting point is to open or reference
this repository in Codex, ask Codex to explain whether it fits your workflow, and then decide
whether to install it.

## Recommended: Ask Codex Directly

### 1. Understand the repository

Send this to Codex:

```text
Read AnonymXXX/codex-harness-engineering and explain what this repository does, which problems it
solves, its core components, who it is for, and its limitations. Cite specific files from the
repository as evidence instead of only repeating the README.
```

If the repository is already open in Codex, replace its name with "the current repository."

### 2. Analyze the benefits and changes for you

Ask Codex to compare the Harness with the configuration and usage context currently available to it:

```text
Read this repository. Within the scope I authorize and that the current environment can access,
inspect my Codex configuration, installed skills, workflows, and recent usage records. Analyze how
my daily Codex usage would change if I adopted this Harness Engineering setup.

Organize the result as "Current state, Changes after adoption, Practical benefits, Costs or risks,
Recommendation." Cite specific repository files as evidence. Clearly state which records you cannot
access, and do not guess.
```

Codex should compare at least these areas:

| Area | Potential change after adoption |
| --- | --- |
| Risk control | Select Fast, Standard, or Heavy Lane checks and use isolated Git worktrees for medium- and high-risk tasks when needed. |
| Skill routing | Choose focused workflows for code design, diagnosis, domain modeling, TDD, and related work. |
| Validation | Run the smallest credible test, lint, build, or Doctor checks for the affected surface. |
| Git and platform operations | Use reusable workflows for commits, GitHub operations, and releases with explicit stop conditions. |
| Parallel execution | Delegate bounded, independently verifiable work to `luna_worker` or `terra_worker`, with the main agent reviewing and integrating it. |
| Knowledge capture | Add only long-lived rules and decisions that pass the Capture Gate, reducing documentation noise. |
| Recovery and upgrades | Restore the workflow on a new machine through versioned configuration, an installer, backups, and health checks. |

These are workflow capabilities, not mechanisms that every task must use. Simple tasks should remain lightweight.

### 3. Ask Codex to adopt it safely

After deciding that it fits, Codex can perform the inspection, installation, and validation:

```text
Help me adopt AnonymXXX/codex-harness-engineering.

First, inspect ~/.codex, ~/.agents/skills, the current Git state, and potential conflicts without
making changes. Compare core and daily, and recommend a profile. If I separately provide a private
overlay path and profile, inspect only that local source; do not attempt to discover or clone other
private repositories. Do not read, copy, or output credentials, sessions, memory, caches, or other
sensitive runtime data.

Before changing anything, list the affected files, backup strategy, dependencies, and risks. Do not
install or rewrite files until I confirm. After confirmation, run harness_setup.py install, followed
by the matching check, Skill index checks, and Harness Doctor. Finally, summarize the actual changes,
backup locations, validation results, and whether I need to start a new Codex task to load the rules
and skills.
```

Codex can analyze only content you explicitly authorize in the current task and that the local
environment can access. You must supply inaccessible history, remote data, or configuration from
other devices; Codex should not infer conclusions from missing information.

## Profiles

- `core`: global Harness rules, workflows, `luna_worker` and `terra_worker`, and five core skills for Harness
  Engineering, code design, diagnosis, domain modeling, and TDD.
- `daily`: includes `core` and adds frequently used skills for Git, GitHub, releases, web access,
  frontend work, and WeChat Mini Programs.
- Private overlay: an optional external skill repository that the user clones and identifies with
  an explicit local path and profile. This repository stores none of its addresses, skill catalog,
  or credential metadata.

See [docs/SKILLS.md](docs/SKILLS.md) for the complete public skill inventory.

## Manual Installation

To install without asking Codex to operate it, first install Codex CLI, Git, Python 3, and GitHub CLI
on macOS, then run:

```bash
gh repo clone AnonymXXX/codex-harness-engineering ~/.local/share/codex-harness-engineering
python3 ~/.local/share/codex-harness-engineering/scripts/harness_setup.py install --profile core
python3 ~/.local/share/codex-harness-engineering/scripts/harness_setup.py check --profile core
```

Replace `core` with `daily` to install the daily extensions. If you have already cloned a private
overlay, pass its local path and profile explicitly:

```bash
python3 ~/.local/share/codex-harness-engineering/scripts/harness_setup.py install --profile daily --overlay-source /absolute/path/to/private-overlay --overlay-profile private
python3 ~/.local/share/codex-harness-engineering/scripts/harness_setup.py check --profile daily --overlay-source /absolute/path/to/private-overlay --overlay-profile private
```

The installer backs up conflicting targets, but it does not copy or overwrite the machine-specific
`~/.codex/config.toml`, credentials, sessions, memory, or caches. After installation, start a new
Codex task to load the global rules, custom agents, and skills.

See [docs/RECOVERY.md](docs/RECOVERY.md) for prerequisites, profile selection, updates, rollback,
and credential handling.

## Layout

- `.codex/`: global agent rules, custom agents, and Harness workflow documents.
- `.agents/skills/`: the Harness skill family and its executable checks.
- `scripts/harness_setup.py`: installation, checks, documentation generation, and local credential setup.
- `profiles.json`: the executable manifest for `core` and `daily`.

The repository mirrors paths relative to the user's home directory. Runtime state, sessions,
memories, credentials, caches, and unrelated skills are intentionally excluded.

## Licensing

Except for the third-party components identified in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), this repository is licensed under the
[Apache License 2.0](LICENSE). First-party authorship and scope are recorded in
[ORIGINAL_WORKS.md](ORIGINAL_WORKS.md). Third-party license terms continue to apply independently
to their identified paths and local derivatives.

## Support

If this project improves your Codex workflow, you can support its ongoing maintenance on
[Afdian](https://afdian.com/a/codexharness). Sponsorship is optional and does not change the
repository's open-source availability or include paid technical support.
