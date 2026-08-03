# Skill Inventory

Generated from `profiles.json` by `scripts/harness_setup.py docs --write`. Do not edit
this file by hand.

## Profiles

- `core`: Global Harness rules, workflows, and five core engineering skills.
- `daily`: Core Harness plus frequently used portable engineering skills. Includes: core.
## Skills

| Profile | Skill | Source | Purpose | Dependencies | Credentials | Validation |
| --- | --- | --- | --- | --- | --- | --- |
| `core` | `codebase-design` | `codex-harness-engineering` | Design deep modules, clean interfaces, adapters, and test seams. | none | none | SKILL.md metadata validation |
| `core` | `diagnosing-bugs` | `codex-harness-engineering` | Diagnose difficult bugs and regressions through reproducible evidence. | none | none | SKILL.md metadata validation |
| `core` | `domain-modeling` | `codex-harness-engineering` | Capture durable domain language, invariants, rules, and decisions. | none | none | SKILL.md metadata validation |
| `core` | `harness-engineering` | `codex-harness-engineering` | Apply the global risk, worktree, documentation, and validation workflow. | git, python3 | none | python3 ~/.agents/skills/harness-engineering/scripts/harness_doctor.py doctor |
| `core` | `tdd` | `codex-harness-engineering` | Implement concrete behavior through a red-green feedback loop. | none | none | SKILL.md metadata validation |
| `daily` | `develop-uniapp-miniapp` | `codex-harness-engineering` | Build and extend uni-app WeChat mini-program projects. | Project-selected Node.js package manager | Project-specific only | SKILL.md metadata validation |
| `daily` | `frontend-design` | `codex-harness-engineering` | Guide intentional visual direction and frontend design decisions. | none | none | SKILL.md metadata validation |
| `daily` | `git-auto-commit` | `codex-harness-engineering` | Group and commit local Git changes conservatively. | git | none | SKILL.md metadata validation |
| `daily` | `github-cli-ops` | `codex-harness-engineering` | Operate GitHub platform workflows through gh and Git. | git, gh | gh auth login | gh auth status |
| `daily` | `release-ops` | `codex-harness-engineering` | Inspect and promote release commits, tags, and branches. | git, python3 | Repository remote authentication | python3 syntax and unit validation |
| `daily` | `web-access` | `codex-harness-engineering` | Perform network research and browser/CDP workflows. | node, curl, Chrome or Edge | Local browser session and ignored config.env preference | node ~/.agents/skills/web-access/scripts/check-deps.mjs |
| `daily` | `wechat-miniprogram-ci-upload` | `codex-harness-engineering` | Upload WeChat Mini Program builds through DevTools CLI or miniprogram-ci. | node, WeChat DevTools | DevTools login or project-local ignored upload key | Dependency and target-project preflight |

## Exclusions

Codex-managed system skills, credentials, sessions, memory, caches, machine-specific
`~/.codex/config.toml`, real env files, and private keys are not distributed.
