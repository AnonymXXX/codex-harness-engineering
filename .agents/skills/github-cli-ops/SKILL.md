---
name: github-cli-ops
description: Operate GitHub platform workflows through the official `gh` CLI and `gh api`, while using plain `git` for repository, branch, remote, clone, fetch, pull, push, checkout, tag, status, diff, log, and commit operations that Git already handles. Use for GitHub repo hosting/settings, issue, pull request, Actions, release, label, milestone, discussion, project, secret, variable, webhook, branch protection, search, gist, notification, and REST/GraphQL API workflows. If the user only asks to stage, commit, or organize local Git changes, use git-auto-commit instead.
---

# GitHub CLI Operations

Use this skill when the user wants the agent to operate GitHub through the official `gh` CLI. Prefer `gh` and `gh api` over browser automation for GitHub platform operations. Use plain `git` for version-control operations that Git can already perform. Use a browser only when the user needs a visual check, screenshot, login UI, or a GitHub website flow that cannot be completed through the CLI/API.


Established user authorization persists for the current task and stated target/impact; do not ask again solely because a later step says “confirm.” Complete safe preparation first. Read-only requests never authorize mutations, and an unclear target or uncovered production, permission, public-sharing, release, or destructive effect still requires explicit authorization.

## Operating Model

1. Resolve the target account, repository, branch, and GitHub object before changing anything.
2. Use `git` first for local repository state, refs, remotes, clones, fetches, pulls, pushes, checkouts, tags, diffs, logs, commits, merges, and rebases.
3. Use `gh` only for GitHub platform objects and APIs: repos as hosted resources, issues, PR metadata/reviews/merge actions, Actions, releases, settings, secrets, variables, collaborators, teams, notifications, search, and REST/GraphQL calls.
4. Use `git-auto-commit` for creating or organizing commits; this skill may inspect Git state but should not invent commit-message policy.
5. Read before write: inspect current state, then perform the smallest necessary operation.
6. Default to private and least exposure. Never make a repo, gist, package, Pages site, release asset, secret, or organization resource public unless the user explicitly asks.
7. Confirm high-impact operations with the user before execution.
8. Verify every write by reading the object back and reporting the final URL/state.

## Preconditions

Check Git before repository/ref operations:

```bash
command -v git
git --version
```

When using SSH remotes, verify GitHub SSH access before cloning or pushing:

```bash
ssh -T git@github.com
git ls-remote git@github.com:OWNER/REPO.git HEAD
```

If SSH is unavailable, use the repo's HTTPS URL from `gh repo view` or ask the user to configure SSH keys. Do not paste private keys into chat.
For `ssh -T git@github.com`, treat GitHub's "successfully authenticated" message as a pass even if the command exits non-zero because GitHub does not provide shell access.

Check `gh` before GitHub platform operations:

```bash
command -v gh
gh --version
gh auth status
```

If `gh auth status` reports no login, stop and tell the user to run:

```bash
gh auth login
```

Do not ask the user to paste tokens into chat. Prefer browser/device-code login handled by `gh`. If an operation fails because of missing scopes, report the exact missing scope or permission and let the user re-authenticate with `gh auth refresh`.

When operating in a local repository, also check:

```bash
git rev-parse --show-toplevel
git status --short
git branch --show-current
git remote -v
```

When a GitHub platform object is involved, also identify the hosted repo:

```bash
gh repo view --json nameWithOwner,url,sshUrl,visibility,defaultBranchRef
```

When outside a repository or when more than one remote could apply, require or infer an explicit `OWNER/REPO` and pass it with `--repo OWNER/REPO` or `-R OWNER/REPO` for `gh` commands.

## Safety Rules

- Never print tokens, secret values, private keys, `.env` contents, or credential files.
- Do not run `git push --force` unless the user explicitly asks for force push and the target branch is confirmed. Prefer `--force-with-lease` when a force push is truly required.
- Do not change repository visibility, transfer/archive/delete a repository, delete branches/tags/releases, rotate or overwrite secrets, change branch protection/rulesets, merge PRs, publish releases, rerun deployment workflows, or invite collaborators without confirming the target and impact with the user.
- Do not use `gh` wrapper commands for work that `git` can do directly. Prefer `git clone`, `git remote`, `git fetch`, `git pull`, `git push`, `git checkout`/`git switch`, `git branch`, `git tag`, `git status`, `git diff`, `git log`, `git commit`, `git merge`, and `git rebase`.
- When creating commits, use the `git-auto-commit` skill's staging and commit-message rules. Do not create ad hoc English commit messages from this skill.
- Create and push Git tags with `git`; create, edit, draft, publish, and upload GitHub Releases with `gh release`.
- Avoid implicit `gh` state. Do not use `gh repo set-default` unless the user explicitly wants to change the default repo.
- For GitHub platform writes, prefer the current repo from `gh repo view`; use explicit `--repo OWNER/REPO` when outside a repo or when ambiguity exists.
- For output parsing, prefer `--json ... --jq ...` over ad hoc text parsing.
- For complex REST or GraphQL operations, use `gh api` with the narrowest endpoint, method, and payload.
- For long Markdown bodies, release notes, comments, or reviews, write a temporary file and use `--body-file`, `--notes-file`, or stdin instead of shell-escaped inline text.
- After writes, read back the changed object with `gh ... view`, `gh ... list`, or `gh api` and verify the expected state.

## Common Commands

Git repository and ref operations:

```bash
git status --short
git remote -v
git remote add origin git@github.com:OWNER/REPO.git
git remote set-url origin git@github.com:OWNER/REPO.git
git clone git@github.com:OWNER/REPO.git
git fetch origin
git pull --ff-only
git push -u origin HEAD
git tag -a TAG -m "Message"
git push origin TAG
git fetch origin pull/NUMBER/head
git switch --detach FETCH_HEAD
```

GitHub repository platform operations:

```bash
gh repo view --json nameWithOwner,url,sshUrl,visibility,defaultBranchRef
gh repo create OWNER/REPO --private
gh repo edit OWNER/REPO --description "Description"
gh repo edit OWNER/REPO --visibility private --accept-visibility-change-consequences
gh repo edit OWNER/REPO --add-topic topic1 --add-topic topic2
```

Issues:

```bash
gh issue list --state open --limit 20 --json number,title,state,url,labels
gh issue view NUMBER --comments
gh issue create --title "Title" --body-file /tmp/issue.md
gh issue edit NUMBER --add-label bug --add-assignee @me
gh issue comment NUMBER --body-file /tmp/comment.md
gh issue close NUMBER --comment "Closing reason"
```

Pull requests:

```bash
gh pr list --state open --limit 20 --json number,title,state,url,headRefName,baseRefName
gh pr view NUMBER --comments --json number,title,state,url,author,headRefName,baseRefName,mergeable,statusCheckRollup
gh pr create --title "Title" --body-file /tmp/pr.md --base BASE_BRANCH --head HEAD_BRANCH
gh pr checks NUMBER
gh pr review NUMBER --comment --body-file /tmp/review.md
gh pr merge NUMBER --squash --delete-branch
```

Actions:

```bash
gh workflow list
gh run list --limit 10 --json databaseId,displayTitle,status,conclusion,workflowName,headBranch,event,url
gh run view RUN_ID --log-failed
gh run rerun RUN_ID --failed
gh workflow run WORKFLOW.yml --ref BRANCH
```

Releases:

```bash
git tag -l TAG
git tag -a TAG -m "Message"
git push origin TAG
gh release list --limit 10
gh release view TAG
gh release create TAG --draft --title "Title" --notes-file /tmp/release-notes.md
gh release upload TAG path/to/asset
gh release edit TAG --draft=false
```

Secrets and variables:

```bash
gh secret list --repo OWNER/REPO
gh secret set NAME --repo OWNER/REPO < /path/to/secret.txt
gh variable list --repo OWNER/REPO
gh variable set NAME --repo OWNER/REPO --body "value"
```

Labels, milestones, and notifications:

```bash
gh label list --repo OWNER/REPO
gh label create NAME --repo OWNER/REPO --color C0FFEE --description "Description"
gh api repos/OWNER/REPO/milestones --jq '.[] | {number,title,state,due_on}'
gh api notifications --jq '.[] | {reason,unread,updated_at,repository: .repository.full_name,subject: .subject.title}'
```

Search and API:

```bash
gh search repos "query" --limit 10 --json fullName,visibility,url,description
gh search issues "query repo:OWNER/REPO" --limit 20 --json number,title,state,url
gh api repos/OWNER/REPO --jq '{full_name, private, visibility, default_branch}'
gh api graphql -f query='query { viewer { login } }'
```

## API Patterns For Website-Like Operations

Use `gh api` for GitHub website settings that have no first-class `gh` command. Prefer `--method PATCH` for edits and read back afterward.

Repository settings:

```bash
gh api repos/OWNER/REPO --jq '{full_name, visibility, has_issues, has_projects, has_wiki, delete_branch_on_merge}'
gh api --method PATCH repos/OWNER/REPO -F has_issues=true -F delete_branch_on_merge=true
```

Branch protection:

```bash
gh api repos/OWNER/REPO/branches/BRANCH/protection
gh api --method PUT repos/OWNER/REPO/branches/BRANCH/protection --input /tmp/branch-protection.json
```

Payload file for `/tmp/branch-protection.json`:

```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": []
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1
  },
  "restrictions": null
}
```

Collaborators and teams:

```bash
gh api repos/OWNER/REPO/collaborators --jq '.[] | {login, permissions}'
gh api --method PUT repos/OWNER/REPO/collaborators/USERNAME -f permission=push
gh api orgs/ORG/teams --jq '.[] | {name, slug}'
gh api --method PUT orgs/ORG/teams/TEAM_SLUG/repos/OWNER/REPO -f permission=push
```

Webhooks, environments, and discussions:

```bash
gh api repos/OWNER/REPO/hooks --jq '.[] | {id, active, events, url: .config.url}'
gh api repos/OWNER/REPO/environments --jq '.environments[] | {name}'
gh api graphql -f query='query($owner:String!, $repo:String!) { repository(owner:$owner, name:$repo) { discussions(first:10) { nodes { number title url } } } }' -f owner=OWNER -f repo=REPO
```

## Workflow Patterns

### Push Current Repo To GitHub

1. Confirm the working directory with `git rev-parse --show-toplevel`.
2. Check `git status --short`, current branch, and `git remote -v`.
3. If no remote exists and the user asked to create a GitHub repo, create only the hosted repo with `gh`, private by default:
   ```bash
   gh repo create OWNER/REPO --private
   ```
4. Read back the hosted repo and choose SSH or HTTPS URL:
   ```bash
   gh repo view OWNER/REPO --json nameWithOwner,sshUrl,url,visibility
   ```
5. If using SSH, verify access:
   ```bash
   ssh -T git@github.com
   git ls-remote git@github.com:OWNER/REPO.git HEAD
   ```
6. Add the Git remote if `origin` does not exist:
   ```bash
   git remote add origin git@github.com:OWNER/REPO.git
   ```
7. If `origin` exists but points to the wrong repo, update it explicitly:
   ```bash
   git remote set-url origin git@github.com:OWNER/REPO.git
   ```
8. Verify the remote points to the intended GitHub repo, then push with `git`:
   ```bash
   git push -u origin HEAD
   ```
9. Verify the hosted repo with `gh repo view --json nameWithOwner,url,sshUrl,visibility,defaultBranchRef`.

### Create An Issue

1. Identify the repo with `gh repo view` or explicit `--repo OWNER/REPO`.
2. Check existing issues to avoid duplicates:
   ```bash
   gh issue list --search "keywords in:title" --state all --json number,title,state,url
   ```
3. Create the body in a temporary Markdown file and run:
   ```bash
   gh issue create --title "Title" --body-file /tmp/issue.md
   ```
4. Read the issue back and return the URL.

### Create A Pull Request

1. Read the default branch from GitHub metadata:
   ```bash
   gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
   ```
2. Confirm the current branch is not the default branch with `git branch --show-current`.
3. Check `git status --short`; do not commit unrelated changes.
4. If the task requires a new commit, use `git-auto-commit` before pushing.
5. Push the branch with `git push -u origin HEAD`.
6. Create the PR with an explicit base and head:
   ```bash
   gh pr create --title "Title" --body-file /tmp/pr.md --base BASE_BRANCH --head HEAD_BRANCH
   ```
7. Return the PR URL and check status with `gh pr checks`.

### Review Or Merge A Pull Request

1. Inspect the PR, diff, reviews, and checks:
   ```bash
   gh pr view NUMBER --comments --json number,title,state,url,author,headRefName,baseRefName,mergeable,statusCheckRollup,reviewDecision
   gh pr checks NUMBER
   ```
2. Fetch and inspect PR code with `git`, not `gh pr checkout`, without overwriting a local branch:
   ```bash
   git fetch origin pull/NUMBER/head
   git switch --detach FETCH_HEAD
   git diff BASE_BRANCH...HEAD
   ```
3. For review comments, use `--body-file`.
4. Before merging, confirm merge method, target branch, CI state, and whether to delete the head branch.
5. Merge only after user confirmation:
   ```bash
   gh pr merge NUMBER --squash --delete-branch
   ```
6. Verify PR state after merge.

### Inspect CI Failure

1. Get recent runs:
   ```bash
   gh run list --limit 10 --json databaseId,displayTitle,status,conclusion,workflowName,headBranch,event,url
   ```
2. Inspect the failing run:
   ```bash
   gh run view RUN_ID --log-failed
   ```
3. Summarize the failing job, exact error, likely cause, and next fix.
4. Do not rerun workflows that deploy, release, or mutate external systems without confirming with the user.

### Create Or Publish A Release

1. Confirm the release tag and target commit with `git`:
   ```bash
   git status --short
   git rev-parse HEAD
   git tag -l TAG
   git ls-remote --tags origin TAG
   ```
2. If the tag does not exist and the user asked to create it, create and push the tag with `git`:
   ```bash
   git tag -a TAG -m "Message"
   git push origin TAG
   ```
3. Create GitHub Releases as drafts by default:
   ```bash
   gh release create TAG --draft --title "Title" --notes-file /tmp/release-notes.md
   ```
4. Do not publish a draft release or mark it latest without explicit user confirmation.
5. Verify the release with `gh release view TAG`.

### Manage Secrets Or Variables

1. Confirm repo/org/environment scope and application scope (`actions`, `dependabot`, `codespaces`, or `agents`).
2. List existing names only; never display values:
   ```bash
   gh secret list --repo OWNER/REPO
   gh variable list --repo OWNER/REPO
   ```
3. Set values through stdin or a local file. Do not echo secret values into the command line.
4. Verify by listing names and metadata only.

### Change Visibility Or Public Exposure

1. Read current visibility:
   ```bash
   gh repo view OWNER/REPO --json nameWithOwner,visibility,url
   ```
2. If making anything public or broadly accessible, stop and ask for explicit confirmation.
3. Run the smallest command needed.
4. Read back `visibility` or access metadata and report the final state.
