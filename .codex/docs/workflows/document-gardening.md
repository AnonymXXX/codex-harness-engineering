# Document Gardening

Keep Harness documentation compact, discoverable, current, and verifiable without adding a heavy review phase to ordinary implementation work.

## Operating Modes

Use a lightweight audit only when the current task changes `AGENTS.md`, changes durable documentation, captures an engineering rule, or closes an execution plan. Inspect the current repository and the files already in scope. For each changed statement, identify its canonical document and check nearby active guidance for duplication, contradiction, and obsolete wording. Do not read Codex memory during an ordinary task.

Use deep gardening only when the user explicitly requests deep gardening, knowledge-base cleanup, or a project-stage closeout. Run the optional read-only Doctor section against the intended repository:

```bash
python3 ~/.agents/skills/harness-engineering/scripts/harness_doctor.py doctor --full --section docs --repo-root <repo>
```

The `docs` section is intentionally excluded from the default core and full Doctor checks. It scans Git-tracked Markdown only. When a linked worktree is passed explicitly, it scans that worktree; when a parent directory is passed, repositories are deduplicated by Git common directory.

## Checks

The deep audit reports:

- missing local Markdown link targets while ignoring external URLs and fenced examples;
- an `AGENTS.md` over 120 lines, which is a prompt to move detailed procedures into linked workflow documents;
- an execution plan under `docs/exec-plans/` that still has an unchecked item more than 30 days after its last commit;
- missing or incomplete Verification metadata in `docs/engineering-rules/`;
- line counts for `~/.codex/memories/memory_summary.md` and `MEMORY.md`, with warnings above 300 and 1000 lines respectively.

Warnings are maintenance prompts, not authorization to change project state. Doctor never edits documentation or memory.

## Engineering Rule Verification

Prefer this explicit mapping in new engineering rules:

```markdown
## Verification

- Mode: automated | manual | not-applicable
- Command: `<deterministic command, or n/a>`
- Reason: <required for manual or not-applicable>
```

Use `automated` only with a runnable deterministic command. Use `manual` when human inspection is essential, and `not-applicable` when the rule cannot meaningfully be tested. Existing non-placeholder command fences remain valid so gardening does not force mechanical migrations.

## Safe Changes

Apply a deterministic, low-risk correction directly when its intended meaning is unambiguous, such as repairing a moved link, updating a document map, filling in a known verification command, or marking a completed plan item.

When the user has explicitly confirmed that a same-scope decision replaces an older one, update or remove the old canonical wording instead of keeping both active; Git history preserves the superseded text. Preserve content and ask before resolving contradictory sources, deleting semantic content without a confirmed replacement, merging rules with different scopes, or choosing which product decision supersedes another. Never automatically edit or delete Codex memory as part of gardening.

Do not create a second source of truth to avoid editing the canonical file. If canonical ownership is unclear or current code, docs, and user direction disagree, stop the documentation change and report the conflict rather than choosing a winner.

## Memory Promotion

Treat memory as a source of candidates, not as project truth. Promote a memory item into versioned project documentation only when current repository evidence confirms that it is durable, reusable, and belongs to that project. Put product behavior in product specs, invariants in engineering rules, resumable work in execution plans, and external material in references.

After promotion, leave memory unchanged unless the user separately requests memory maintenance. This keeps normal task context small and avoids turning uncertain historical notes into active rules.

## Completion

After changing Harness workflows, templates, or skills, run the fast core Doctor and relevant tests. Run the `docs` section only when this workflow's deep mode applies or the current documentation change needs its deterministic checks.
