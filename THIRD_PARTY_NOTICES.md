# Third-Party Notices

This distribution includes the following third-party Agent Skills and local derivatives. Their
license terms apply independently to the paths identified below, including historical paths
retained in Git history, and are not replaced by the repository-level Apache License 2.0.

## frontend-design

- Upstream publisher: Anthropic
- Source: https://github.com/anthropics/skills/tree/main/skills/frontend-design
- Pinned upstream commit: `2235be7c60b551f5de82ade908fd3816455afcda`
- License: Apache License 2.0
- License copy: `.agents/skills/frontend-design/LICENSE.txt`
- Local status: `SKILL.md` is a local derivative, adapted for existing UI conventions,
  proportionate design work, browser-acceptance authorization, and explicit knowledge capture.
  Its original upstream Git blob ID is `decdff43d05908b4c1fc2cfd2d80fc5743440934`.
  `LICENSE.txt` remains an unmodified upstream copy with Git blob ID
  `f433b1a53f5b830a205fd2df78e2b34974656c7b`.

The upstream directory does not contain a `NOTICE` file.

## mattpocock/skills

- Upstream author: Matt Pocock
- Source: https://github.com/mattpocock/skills
- License: MIT
- Comparison reference commit: `e9fcdf95b402d360f90f1db8d776d5dd450f9234`, the latest
  upstream `main` commit preceding the local import
- Local import commit: `7c24ba00f83f4074f56907699162b575e4308e2e` (2026-07-15)
- Repository license copy: `licenses/mattpocock-skills-MIT.txt`

Current local derivative Skills:

- `.agents/skills/codebase-design/` from upstream `skills/engineering/codebase-design/`
- `.agents/skills/diagnosing-bugs/` from upstream `skills/engineering/diagnosing-bugs/`
- `.agents/skills/domain-modeling/` from upstream `skills/engineering/domain-modeling/`
- `.agents/skills/tdd/` from upstream `skills/engineering/tdd/`

Complete MIT terms are also included as `LICENSE.txt` in each current local Skill directory.

Historical local derivative Skills retained only in Git history:

- `.agents/skills/ask-matt/` from upstream `skills/engineering/ask-matt/`
- `.agents/skills/grill-with-docs/` from upstream `skills/engineering/grill-with-docs/`
- `.agents/skills/handoff/` from upstream `skills/productivity/handoff/`

These three directories were removed from the current tree by local commit
`ed27ff886d14ed556cb80dc74484358449578b5d`; the repository license copy above preserves their
MIT terms for historical revisions.

The local distribution adapts the Skill instructions and UI metadata and omits upstream files not
needed by this Harness. The bundled files are local derivatives, not unmodified upstream snapshots.
