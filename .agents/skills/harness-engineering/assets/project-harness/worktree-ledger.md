# Worktree Ledger

## <Task Or Branch>

- Path: `<absolute worktree path>`
- Branch: `<branch>`
- State: clean | dirty | committed-unmerged | stale | missing-on-disk
- Changed summary: <`git status --short` or `git diff --stat` summary>
- Latest validation: `<command>` - pass | fail | not run
- Browser acceptance: not-applicable | pending | passed | failed
- Acceptance evidence: <Agent check result or explicit user acceptance confirmation with task/thread reference, or n/a>
- Integration basis: none | local-only | explicit-request | high-confidence-policy
- Integration authorization: <authorized operation, target, and request/policy reference, or n/a>
- High-confidence evidence: <validation summary; static final-diff review; target branch, or n/a>
- Recommended next step: <continue, review, commit, merge, clean up, or ask>
