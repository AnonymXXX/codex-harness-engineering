# Worktree Ledger

## <Task Or Branch>

- Path: `<absolute worktree path>`
- Branch: `<branch>`
- State: clean | dirty | committed-unmerged | stale | missing-on-disk
- Changed summary: <`git status --short` or `git diff --stat` summary>
- Latest validation: `<command>` - pass | fail | not run
- Browser acceptance: not-applicable | pending | passed | waived-by-high-confidence
- Acceptance confirmation: <task/thread reference and user confirmation or explicit push request, or n/a>
- High-confidence evidence: <validation summary; static final-diff review; target branch, or n/a>
- Recommended next step: <continue, review, commit, merge, clean up, or ask>
