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
| Parallel execution | Subagent delegation is paused (2026-08-06); the main agent completes work directly, and the previous Worker protocol remains recoverable from Git history. |
| Knowledge capture | Add only long-lived rules and decisions that pass the Capture Gate, reducing documentation noise. |
| Recovery and upgrades | Keep a single source of truth through versioned configuration and symlinks; the historical one-command installer remains recoverable from Git history. |

These are workflow capabilities, not mechanisms that every task must use. Simple tasks should remain lightweight.

### 3. Ask Codex to adopt it safely

After deciding that it fits, Codex can perform the inspection, linking, and validation:

```text
Help me adopt AnonymXXX/codex-harness-engineering.

First, inspect ~/.codex, ~/.agents/skills, the current Git state, and potential conflicts without
making changes. Do not read, copy, or output credentials, sessions, memory, caches, or other
sensitive runtime data.

Before changing anything, list the affected files, backup strategy, dependencies, and risks. Do not
create symlinks or rewrite files until I confirm. After confirmation, create the documented symlinks,
then run the Skill index checks and Harness Doctor. Finally, summarize the actual changes, validation
results, and whether I need to start a new Codex task to load the rules and skills.
```

Codex can analyze only content you explicitly authorize in the current task and that the local
environment can access. You must supply inaccessible history, remote data, or configuration from
other devices; Codex should not infer conclusions from missing information.

## Skill Set

- Core workflow: `harness-engineering`, plus the four core engineering skills
  `codebase-design`, `diagnosing-bugs`, `domain-modeling`, and `tdd`.
- Frequently used domain skills: `git-auto-commit`, `github-cli-ops`, `release-ops`, `ego-browser`,
  `frontend-design`, `develop-uniapp-miniapp`, and `wechat-miniprogram-ci-upload`.

## Installation

If this machine is already installed, use it directly. To set up a new machine, first install Codex
CLI, Git, `uv`, GitHub CLI, and ego lite on macOS, then create the Harness symlinks manually.
`ego-browser` is supplied by ego lite and is not copied from this repository:

```bash
gh repo clone AnonymXXX/codex-harness-engineering ~/.local/share/codex-harness-engineering
ln -s ~/.local/share/codex-harness-engineering/.codex/AGENTS.md ~/.codex/AGENTS.md
ln -s ~/.local/share/codex-harness-engineering/.codex/docs ~/.codex/docs
for skill in ~/.local/share/codex-harness-engineering/.agents/skills/*; do
  ln -s "$skill" ~/.agents/skills/
done
uv run ~/.agents/skills/harness-engineering/scripts/harness_doctor.py index --write
uv run ~/.agents/skills/harness-engineering/scripts/harness_doctor.py index --check
uv run ~/.agents/skills/harness-engineering/scripts/harness_doctor.py doctor
```

If a link target already exists, back it up with `/usr/bin/trash` before linking. The installer does
not copy or overwrite the machine-specific `~/.codex/config.toml`, credentials, sessions, memory, or
caches. After installation, start a new Codex task to load the global rules and skills.

Historical releases provide the one-command installer `scripts/harness_setup.py` and `profiles.json`.
To automate installation, restore those two files from Git history and follow the README of that era.

## Layout

- `.codex/`: global agent rules and Harness workflow documents.
- `.agents/skills/`: the Harness skill family and its executable checks.

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
