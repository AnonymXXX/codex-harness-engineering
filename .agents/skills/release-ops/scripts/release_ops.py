#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


SEMVER_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
VAGUE_FEATURE_KEYWORDS = {"优化", "修改", "调整"}
MAJOR_SIGNALS = (
    "breaking",
    "不兼容",
    "移除旧逻辑",
    "remove old behavior",
    "replace old behavior",
)
MINOR_SIGNALS = (
    "feat",
    "新增",
    "增加",
    "支持",
    "new page",
    "new module",
    "new menu",
    "new feature",
    "export",
)
PATCH_SIGNALS = (
    "fix",
    "修复",
    "样式",
    "文案",
    "判空",
    "guard",
    "display",
    "显示",
    "copy",
    "style",
)


class GitCommandError(RuntimeError):
    pass


@dataclass
class Defaults:
    defaultAuthorName: str
    defaultSourceBranch: str
    timezone: str
    targetBranchPriority: list[str]
    pendingCommitConfirmThreshold: int
    featureWindowExpansionWeeks: dict[str, int]
    tagStyle: str
    missingRule: str
    allowDirectPushTargets: list[str]


@dataclass
class Commit:
    sha: str
    author: str
    authored_at: str
    subject: str
    body: str
    files: list[str] = field(default_factory=list)
    diff: str = ""

    def authored_datetime(self) -> datetime:
        return datetime.fromisoformat(self.authored_at)

    def combined_text(self) -> str:
        return "\n".join((self.subject, self.body, self.diff)).lower()


@dataclass
class Analysis:
    mode: str
    repo: str
    source_branch: str
    source_ref: str
    target_branch: str
    target_ref: str
    author: str
    since: str | None
    until: str | None
    feature: str | None
    commit_selectors: list[str]
    pending_count: int
    pending_commits: list[Commit]
    related_other_author_commits: list[Commit]
    suggested_bump: str | None
    bump_confidence: str | None
    blockers: list[str]
    warnings: list[str]
    threshold_exceeded: bool
    needs_confirmation: bool
    latest_reachable_tag: str | None
    proposed_tag: str | None
    matched_count: int
    selected_cluster_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect or execute release backport operations.",
    )
    parser.add_argument("mode", choices=("inspect", "execute"))
    parser.add_argument("--repo", default=os.getcwd(), help="Git repository path.")
    parser.add_argument("--source-branch", help="Source branch name. Defaults from config.")
    parser.add_argument(
        "--target-branch",
        help="Target production branch. Auto-detected when omitted.",
    )
    parser.add_argument(
        "--author",
        help="Git author name. Defaults to repo git config user.name, then config.",
    )
    parser.add_argument(
        "--since",
        help="Start time in YYYY-MM-DD or ISO datetime. Assumes configured timezone when missing.",
    )
    parser.add_argument(
        "--until",
        help="End time in YYYY-MM-DD or ISO datetime. Assumes configured timezone when missing.",
    )
    parser.add_argument(
        "--feature",
        help="Feature keyword used for commit message/diff/path matching.",
    )
    parser.add_argument(
        "--commit",
        dest="commit_shas",
        action="append",
        default=[],
        help="Exact source commit to include. Repeat to batch multiple commits under one tag.",
    )
    parser.add_argument(
        "--bump",
        choices=("major", "minor", "patch", "auto"),
        default="auto",
        help="Requested SemVer bump. Defaults to auto inference.",
    )
    parser.add_argument(
        "--confirm-all",
        action="store_true",
        help="Allow execute mode to continue when pending commits exceed the threshold.",
    )
    parser.add_argument(
        "--sync-target",
        action="store_true",
        help="Fast-forward the local target branch to origin before execute mode when safe.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output.",
    )
    return parser.parse_args()


def run_cmd(repo: Path, args: list[str], check: bool = True) -> str:
    result = subprocess.run(
        args,
        cwd=repo,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        details = stderr or stdout or f"command failed: {' '.join(args)}"
        raise GitCommandError(details)
    return result.stdout


def current_branch(repo: Path) -> str:
    return run_cmd(repo, ["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()


def load_defaults(skill_dir: Path) -> Defaults:
    defaults_path = skill_dir / "assets" / "defaults.json"
    payload = json.loads(defaults_path.read_text())
    return Defaults(**payload)


def current_git_author(repo: Path) -> str | None:
    author = run_cmd(repo, ["git", "config", "user.name"], check=False).strip()
    return author or None


def resolve_author(repo: Path, explicit: str | None, defaults: Defaults) -> str:
    if explicit:
        return explicit
    return current_git_author(repo) or defaults.defaultAuthorName


def parse_time(value: str, timezone: ZoneInfo, is_end: bool) -> datetime:
    if not value:
        raise ValueError("time value is empty")
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone)
        return dt
    except ValueError:
        pass

    try:
        dt = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone)
        if is_end:
            dt = dt.replace(hour=23, minute=59, second=59)
        return dt
    except ValueError as exc:
        raise ValueError(f"unsupported time format: {value}") from exc


def iso_or_none(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def tokenize_feature(feature: str) -> list[str]:
    cleaned = feature.strip().lower()
    tokens = [part for part in re.split(r"[\s,/_:|.-]+", cleaned) if part]
    if not tokens and cleaned:
        return [cleaned]
    return tokens


def is_vague_feature(feature: str | None) -> bool:
    if not feature:
        return False
    tokens = tokenize_feature(feature)
    return len(tokens) == 1 and tokens[0] in VAGUE_FEATURE_KEYWORDS


def maybe_ref(repo: Path, ref: str) -> bool:
    return subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        cwd=repo,
        text=True,
        capture_output=True,
    ).returncode == 0


def resolve_branch_ref(repo: Path, branch: str) -> str:
    remote_ref = f"origin/{branch}"
    if maybe_ref(repo, remote_ref):
        return remote_ref
    if maybe_ref(repo, branch):
        return branch
    raise GitCommandError(f"branch not found: {branch}")


def resolve_source_branch(
    repo: Path,
    explicit: str | None,
    defaults: Defaults,
) -> tuple[str | None, str | None, str | None]:
    branch = explicit or defaults.defaultSourceBranch
    try:
        ref = resolve_branch_ref(repo, branch)
        return branch, ref, None
    except GitCommandError:
        if explicit:
            raise
        return None, None, f"default source branch does not exist: {branch}; ask the user to specify the source branch"


def resolve_target_branch(repo: Path, explicit: str | None, defaults: Defaults) -> tuple[str, str]:
    if explicit:
        return explicit, resolve_branch_ref(repo, explicit)

    for branch in defaults.targetBranchPriority:
        try:
            return branch, resolve_branch_ref(repo, branch)
        except GitCommandError:
            continue
    raise GitCommandError("none of the target production branches exist")


def normalize_branch(branch_or_ref: str) -> str:
    return branch_or_ref.removeprefix("origin/")


def fetch_and_check_clean(repo: Path) -> None:
    run_cmd(repo, ["git", "fetch", "--all", "--prune", "--tags"])
    status = run_cmd(repo, ["git", "status", "--porcelain"])
    if status.strip():
        raise GitCommandError("working tree is not clean")


def list_commits(repo: Path, ref: str, since: datetime | None, until: datetime | None) -> list[Commit]:
    format_str = "%H%x1f%an%x1f%aI%x1f%s%x1f%b%x1e"
    cmd = ["git", "log", ref, f"--pretty=format:{format_str}", "--date=iso-strict"]
    if since:
        cmd.append(f"--since={since.isoformat()}")
    if until:
        cmd.append(f"--until={until.isoformat()}")
    raw = run_cmd(repo, cmd)
    commits: list[Commit] = []
    for record in raw.split("\x1e"):
        # Preserve field separators so commits with an empty body still keep the
        # trailing fifth column from the pretty format output.
        record = record.strip("\r\n")
        if not record:
            continue
        parts = record.split("\x1f")
        if len(parts) < 5:
            continue
        sha, author, authored_at, subject, body = parts[:5]
        files = [
            line.strip()
            for line in run_cmd(
                repo,
                ["git", "show", "--format=", "--name-only", "--no-renames", sha],
            ).splitlines()
            if line.strip()
        ]
        diff = run_cmd(
            repo,
            ["git", "show", "--format=", "--unified=0", "--no-color", sha],
        )
        commits.append(
            Commit(
                sha=sha,
                author=author,
                authored_at=authored_at,
                subject=subject.strip(),
                body=body.strip(),
                files=files,
                diff=diff,
            )
        )
    commits.sort(key=lambda item: item.authored_datetime())
    return commits


def read_commit(repo: Path, sha: str) -> Commit:
    format_str = "%H%x1f%an%x1f%aI%x1f%s%x1f%b"
    raw = run_cmd(
        repo,
        ["git", "show", "-s", f"--pretty=format:{format_str}", "--date=iso-strict", sha],
    ).strip("\r\n")
    parts = raw.split("\x1f")
    if len(parts) < 5:
        raise GitCommandError(f"could not read commit metadata: {sha}")
    resolved_sha, author, authored_at, subject, body = parts[:5]
    files = [
        line.strip()
        for line in run_cmd(
            repo,
            ["git", "show", "--format=", "--name-only", "--no-renames", resolved_sha],
        ).splitlines()
        if line.strip()
    ]
    diff = run_cmd(
        repo,
        ["git", "show", "--format=", "--unified=0", "--no-color", resolved_sha],
    )
    return Commit(
        sha=resolved_sha,
        author=author,
        authored_at=authored_at,
        subject=subject.strip(),
        body=body.strip(),
        files=files,
        diff=diff,
    )


def resolve_explicit_commits(repo: Path, source_ref: str, selectors: list[str]) -> list[Commit]:
    resolved: dict[str, Commit] = {}
    for selector in selectors:
        sha = run_cmd(
            repo,
            ["git", "rev-parse", "--verify", f"{selector}^{{commit}}"],
            check=False,
        ).strip()
        if not sha:
            raise GitCommandError(f"commit not found: {selector}")
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", sha, source_ref],
            cwd=repo,
            text=True,
            capture_output=True,
        )
        if ancestor.returncode != 0:
            raise GitCommandError(f"commit is not reachable from {source_ref}: {selector}")
        resolved.setdefault(sha, read_commit(repo, sha))

    source_order = {
        sha: index
        for index, sha in enumerate(
            run_cmd(repo, ["git", "rev-list", "--reverse", source_ref]).splitlines()
        )
    }
    return sorted(resolved.values(), key=lambda commit: source_order[commit.sha])


def plus_commits_from_git_cherry(repo: Path, target_ref: str, source_ref: str) -> set[str]:
    raw = run_cmd(repo, ["git", "cherry", target_ref, source_ref])
    pending: set[str] = set()
    for line in raw.splitlines():
        line = line.strip()
        if not line or not line.startswith("+ "):
            continue
        parts = line.split()
        if len(parts) >= 2:
            pending.add(parts[1])
    return pending


def feature_score(feature: str, commit: Commit) -> int:
    text = commit.combined_text()
    phrase = feature.strip().lower()
    tokens = tokenize_feature(feature)
    score = 0
    if phrase and phrase in text:
        score += 100
    for token in tokens:
        if token in text:
            score += 10
    return score


def share_files(left: Commit, right: Commit) -> bool:
    return bool(set(left.files) & set(right.files))


def connected_components(commits: list[Commit]) -> list[list[Commit]]:
    if not commits:
        return []
    by_sha = {commit.sha: commit for commit in commits}
    neighbors: dict[str, set[str]] = {commit.sha: set() for commit in commits}
    for idx, left in enumerate(commits):
        for right in commits[idx + 1 :]:
            if share_files(left, right):
                neighbors[left.sha].add(right.sha)
                neighbors[right.sha].add(left.sha)
    seen: set[str] = set()
    components: list[list[Commit]] = []
    for commit in commits:
        if commit.sha in seen:
            continue
        stack = [commit.sha]
        component: list[Commit] = []
        seen.add(commit.sha)
        while stack:
            current = stack.pop()
            component.append(by_sha[current])
            for neighbor in neighbors[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        component.sort(key=lambda item: item.authored_datetime())
        components.append(component)
    components.sort(key=lambda group: group[0].authored_datetime())
    return components


def expand_cluster(seed_commits: list[Commit], author_commits: list[Commit]) -> list[Commit]:
    if not seed_commits:
        return []
    selected = {commit.sha: commit for commit in seed_commits}
    changed = True
    while changed:
        changed = False
        current = list(selected.values())
        selected_files = set()
        for commit in current:
            selected_files.update(commit.files)
        for commit in author_commits:
            if commit.sha in selected:
                continue
            if selected_files & set(commit.files):
                selected[commit.sha] = commit
                changed = True
    return sorted(selected.values(), key=lambda item: item.authored_datetime())


def infer_bump(commits: list[Commit]) -> tuple[str | None, str | None]:
    if not commits:
        return None, None
    highest = "patch"
    confidence = "low"
    for commit in commits:
        text = commit.combined_text()
        if any(signal in text for signal in MAJOR_SIGNALS):
            return "major", "high"
        if any(signal in text for signal in MINOR_SIGNALS):
            highest = "minor"
            confidence = "high"
            continue
        if any(signal in text for signal in PATCH_SIGNALS):
            if highest != "minor":
                highest = "patch"
            if confidence != "high":
                confidence = "high"
            continue
        if highest == "patch" and confidence != "high":
            confidence = "low"
    return highest, confidence


def increment_semver(tag: str, bump: str) -> str:
    match = SEMVER_RE.match(tag)
    if not match:
        raise ValueError(f"tag is not semver: {tag}")
    major, minor, patch = (int(part) for part in match.groups())
    if bump == "major":
        return f"v{major + 1}.0.0"
    if bump == "minor":
        return f"v{major}.{minor + 1}.0"
    if bump == "patch":
        return f"v{major}.{minor}.{patch + 1}"
    raise ValueError(f"unsupported bump: {bump}")


def latest_reachable_tag(repo: Path, ref: str) -> str | None:
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0", ref],
        cwd=repo,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def tag_exists_local(repo: Path, tag: str) -> bool:
    return maybe_ref(repo, f"refs/tags/{tag}")


def tag_exists_remote(repo: Path, tag: str) -> bool:
    raw = run_cmd(repo, ["git", "ls-remote", "--tags", "origin", tag], check=False)
    return bool(raw.strip())


def detect_related_other_author_commits(
    commits: list[Commit],
    feature: str | None,
    pending_shas: set[str],
    author: str,
    selected_commits: list[Commit],
) -> list[Commit]:
    if not feature:
        return []
    selected_files = set()
    for commit in selected_commits:
        selected_files.update(commit.files)
    related: list[Commit] = []
    for commit in commits:
        if commit.author == author or commit.sha not in pending_shas:
            continue
        score = feature_score(feature, commit)
        overlap = bool(selected_files & set(commit.files))
        if score > 0 or overlap:
            related.append(commit)
    related.sort(key=lambda item: item.authored_datetime())
    return related


def choose_feature_commits(
    author_commits: list[Commit],
    pending_shas: set[str],
    feature: str,
) -> tuple[list[Commit], int, bool, list[str]]:
    warnings: list[str] = []
    seed_commits = [commit for commit in author_commits if feature_score(feature, commit) > 0]
    if not seed_commits:
        return [], 0, False, warnings
    selected = expand_cluster(seed_commits, author_commits)
    components = connected_components(selected)
    if len(components) <= 1:
        return selected, len(components), False, warnings

    pending_components = [
        component
        for component in components
        if any(commit.sha in pending_shas for commit in component)
    ]
    if len(pending_components) == 1:
        warnings.append("multiple clusters matched; selected the only cluster with pending commits")
        return pending_components[0], len(components), False, warnings
    return selected, len(components), True, warnings


def build_analysis(args: argparse.Namespace, skill_dir: Path) -> Analysis:
    repo = Path(args.repo).resolve()
    defaults = load_defaults(skill_dir)
    timezone = ZoneInfo(defaults.timezone)
    fetch_and_check_clean(repo)

    blockers: list[str] = []
    warnings: list[str] = []

    source_branch, source_ref, source_blocker = resolve_source_branch(repo, args.source_branch, defaults)
    if source_blocker:
        blockers.append(source_blocker)
    target_branch, target_ref = resolve_target_branch(repo, args.target_branch, defaults)
    author = resolve_author(repo, args.author, defaults)

    if not args.feature and not args.since and not args.until and not args.commit_shas:
        blockers.append("missing selector: provide a time range, feature keyword, or --commit")

    if args.commit_shas and (args.feature or args.since or args.until):
        blockers.append("--commit cannot be combined with --feature, --since, or --until")

    if is_vague_feature(args.feature):
        blockers.append("feature keyword is too vague and needs confirmation")

    requested_since = parse_time(args.since, timezone, is_end=False) if args.since else None
    requested_until = parse_time(args.until, timezone, is_end=True) if args.until else None
    if requested_since and requested_until and requested_since > requested_until:
        raise ValueError("--since must be earlier than --until")

    now = datetime.now(timezone)
    windows: list[tuple[datetime | None, datetime | None]] = []
    if args.feature and not requested_since and not requested_until:
        step = defaults.featureWindowExpansionWeeks["step"]
        max_weeks = defaults.featureWindowExpansionWeeks["max"]
        for week in range(step, max_weeks + 1, step):
            windows.append((now - timedelta(weeks=week), now))
    else:
        windows.append((requested_since, requested_until))

    if source_ref is None or source_branch is None:
        return Analysis(
            mode=args.mode,
            repo=str(repo),
            source_branch=defaults.defaultSourceBranch,
            source_ref="",
            target_branch=target_branch,
            target_ref=target_ref,
            author=author,
            since=iso_or_none(requested_since),
            until=iso_or_none(requested_until),
            feature=args.feature,
            commit_selectors=args.commit_shas,
            pending_count=0,
            pending_commits=[],
            related_other_author_commits=[],
            suggested_bump=None,
            bump_confidence=None,
            blockers=sorted(set(blockers)),
            warnings=sorted(set(warnings)),
            threshold_exceeded=False,
            needs_confirmation=True,
            latest_reachable_tag=None,
            proposed_tag=None,
            matched_count=0,
            selected_cluster_count=0,
        )

    all_pending_shas = plus_commits_from_git_cherry(repo, target_ref, source_ref)
    matched_commits: list[Commit] = []
    selected_cluster_count = 0
    related_other_author_commits: list[Commit] = []
    used_since: datetime | None = None
    used_until: datetime | None = None

    if args.commit_shas:
        matched_commits = resolve_explicit_commits(repo, source_ref, args.commit_shas)
        mismatched_authors = sorted({commit.author for commit in matched_commits if commit.author != author})
        if mismatched_authors:
            blockers.append(
                "explicit commits include authors outside the selected author: "
                + ", ".join(mismatched_authors)
            )
    else:
        for window_since, window_until in windows:
            commits_in_window = list_commits(repo, source_ref, window_since, window_until)
            author_commits = [commit for commit in commits_in_window if commit.author == author]
            if not args.feature:
                matched_commits = author_commits
            else:
                (
                    matched_commits,
                    selected_cluster_count,
                    ambiguous_clusters,
                    feature_warnings,
                ) = choose_feature_commits(
                    author_commits,
                    all_pending_shas,
                    args.feature,
                )
                warnings.extend(feature_warnings)
                if args.mode == "execute" and ambiguous_clusters:
                    blockers.append("multiple unrelated feature clusters matched")
                related_other_author_commits = detect_related_other_author_commits(
                    commits_in_window,
                    args.feature,
                    all_pending_shas,
                    author,
                    matched_commits,
                )
                if args.mode == "execute" and related_other_author_commits:
                    blockers.append("related commits from other authors were detected")

            pending_commits = [
                commit
                for commit in matched_commits
                if commit.sha in all_pending_shas
            ]
            if pending_commits:
                used_since = window_since
                used_until = window_until
                matched_commits = pending_commits if not args.feature else matched_commits
                break

    if used_since is None and used_until is None and windows:
        used_since, used_until = windows[-1]

    if args.feature and matched_commits:
        pending_commits = [commit for commit in matched_commits if commit.sha in all_pending_shas]
    else:
        pending_commits = [commit for commit in matched_commits if commit.sha in all_pending_shas]

    threshold_exceeded = len(pending_commits) > defaults.pendingCommitConfirmThreshold
    if args.mode == "execute" and threshold_exceeded and not args.confirm_all:
        blockers.append("pending commit count exceeds confirmation threshold")

    suggested_bump: str | None
    bump_confidence: str | None
    if args.bump != "auto":
        suggested_bump = args.bump
        bump_confidence = "explicit"
    else:
        suggested_bump, bump_confidence = infer_bump(pending_commits)
        if args.mode == "execute" and pending_commits and bump_confidence == "low":
            blockers.append("bump inference is low confidence")

    latest_tag = None
    proposed_tag = None
    if pending_commits and (args.mode == "execute" or suggested_bump):
        latest_tag = latest_reachable_tag(repo, target_ref)
        if latest_tag is None:
            blockers.append("could not find a reachable tag on the target branch")
        elif not SEMVER_RE.match(latest_tag):
            blockers.append(f"latest reachable tag is not semver: {latest_tag}")
        elif suggested_bump:
            proposed_tag = increment_semver(latest_tag, suggested_bump)
            if tag_exists_local(repo, proposed_tag) or tag_exists_remote(repo, proposed_tag):
                blockers.append(f"target tag already exists: {proposed_tag}")

    if args.mode == "execute" and related_other_author_commits:
        warnings.append("execution requires user confirmation because related other-author commits exist")

    return Analysis(
        mode=args.mode,
        repo=str(repo),
        source_branch=source_branch,
        source_ref=source_ref,
        target_branch=target_branch,
        target_ref=target_ref,
        author=author,
        since=iso_or_none(used_since),
        until=iso_or_none(used_until),
        feature=args.feature,
        commit_selectors=args.commit_shas,
        pending_count=len(pending_commits),
        pending_commits=pending_commits,
        related_other_author_commits=related_other_author_commits,
        suggested_bump=suggested_bump,
        bump_confidence=bump_confidence,
        blockers=sorted(set(blockers)),
        warnings=sorted(set(warnings)),
        threshold_exceeded=threshold_exceeded,
        needs_confirmation=bool(blockers),
        latest_reachable_tag=latest_tag,
        proposed_tag=proposed_tag,
        matched_count=len(matched_commits),
        selected_cluster_count=selected_cluster_count,
    )


def ensure_local_target_branch(repo: Path, branch: str, sync_target: bool = False) -> None:
    remote_ref = f"origin/{branch}"
    if not maybe_ref(repo, remote_ref):
        raise GitCommandError(f"remote target branch does not exist: {remote_ref}")

    local_exists = maybe_ref(repo, branch)
    remote_sha = run_cmd(repo, ["git", "rev-parse", remote_ref]).strip()
    if local_exists:
        local_sha = run_cmd(repo, ["git", "rev-parse", branch]).strip()
        if local_sha != remote_sha:
            ahead_behind = run_cmd(
                repo,
                ["git", "rev-list", "--left-right", "--count", f"{branch}...{remote_ref}"],
            ).strip()
            ahead, behind = (int(part) for part in ahead_behind.split())
            if sync_target and ahead == 0 and behind > 0:
                run_cmd(repo, ["git", "switch", branch])
                run_cmd(repo, ["git", "merge", "--ff-only", remote_ref])
                return
            raise GitCommandError(
                f"local branch {branch} is not aligned with {remote_ref}; sync it before execute mode"
            )
        run_cmd(repo, ["git", "switch", branch])
        return

    run_cmd(repo, ["git", "switch", "-c", branch, "--track", remote_ref])


def cherry_pick_commits(repo: Path, commits: list[Commit]) -> None:
    for commit in commits:
        result = subprocess.run(
            ["git", "cherry-pick", commit.sha],
            cwd=repo,
            text=True,
            capture_output=True,
        )
        if result.returncode == 0:
            continue
        conflict_files = run_cmd(
            repo,
            ["git", "diff", "--name-only", "--diff-filter=U"],
            check=False,
        ).strip()
        subprocess.run(
            ["git", "cherry-pick", "--abort"],
            cwd=repo,
            text=True,
            capture_output=True,
        )
        details = result.stderr.strip() or result.stdout.strip() or "unknown cherry-pick failure"
        if conflict_files:
            details = f"{details}; conflict files: {conflict_files}"
        raise GitCommandError(f"failed to cherry-pick {commit.sha}: {details}")


def execute_plan(repo: Path, analysis: Analysis, sync_target: bool = False) -> dict[str, Any]:
    original_branch = current_branch(repo)
    restored_branch = original_branch
    try:
        ensure_local_target_branch(repo, analysis.target_branch, sync_target=sync_target)
        cherry_pick_commits(repo, analysis.pending_commits)
        if analysis.proposed_tag is None:
            raise GitCommandError("missing proposed tag in execute mode")
        run_cmd(repo, ["git", "tag", analysis.proposed_tag])
        run_cmd(repo, ["git", "push", "origin", analysis.target_branch, analysis.proposed_tag])
        remote_branch_sha = run_cmd(
            repo,
            ["git", "ls-remote", "--heads", "origin", analysis.target_branch],
        ).strip()
        remote_tag_sha = run_cmd(
            repo,
            ["git", "ls-remote", "--tags", "origin", analysis.proposed_tag],
        ).strip()
    finally:
        try:
            current = current_branch(repo)
            if current != original_branch and maybe_ref(repo, original_branch):
                run_cmd(repo, ["git", "switch", original_branch])
                restored_branch = original_branch
            else:
                restored_branch = current
        except Exception:
            restored_branch = "<restore-failed>"

    return {
        "pushedBranch": analysis.target_branch,
        "pushedTag": analysis.proposed_tag,
        "remoteBranchRef": remote_branch_sha,
        "remoteTagRef": remote_tag_sha,
        "restoredBranch": restored_branch,
    }


def analysis_to_jsonable(analysis: Analysis) -> dict[str, Any]:
    payload = asdict(analysis)
    payload["pending_commits"] = [
        {"sha": commit.sha, "subject": commit.subject}
        for commit in analysis.pending_commits
    ]
    payload["related_other_author_commits"] = [
        {
            "sha": commit.sha,
            "author": commit.author,
            "subject": commit.subject,
        }
        for commit in analysis.related_other_author_commits
    ]
    return payload


def print_text_report(analysis: Analysis, execution: dict[str, Any] | None = None) -> None:
    lines = [
        f"mode: {analysis.mode}",
        f"repo: {analysis.repo}",
        f"source: {analysis.source_ref}",
        f"target: {analysis.target_ref}",
        f"author: {analysis.author}",
    ]
    if analysis.since or analysis.until:
        lines.append(f"time_window: {analysis.since or '-'} -> {analysis.until or '-'}")
    if analysis.feature:
        lines.append(f"feature: {analysis.feature}")
    if analysis.commit_selectors:
        lines.append("commit_selectors: " + ", ".join(analysis.commit_selectors))
    lines.append(f"pending_count: {analysis.pending_count}")
    if analysis.pending_commits:
        lines.append("pending_commits:")
        for commit in analysis.pending_commits:
            lines.append(f"  - {commit.sha[:12]} {commit.subject}")
    if analysis.related_other_author_commits:
        lines.append("related_other_author_commits:")
        for commit in analysis.related_other_author_commits:
            lines.append(f"  - {commit.sha[:12]} {commit.author} {commit.subject}")
    if analysis.suggested_bump:
        lines.append(f"suggested_bump: {analysis.suggested_bump}")
    if analysis.latest_reachable_tag:
        lines.append(f"latest_reachable_tag: {analysis.latest_reachable_tag}")
    if analysis.proposed_tag:
        lines.append(f"proposed_tag: {analysis.proposed_tag}")
    if analysis.warnings:
        lines.append("warnings:")
        for item in analysis.warnings:
            lines.append(f"  - {item}")
    if analysis.blockers:
        lines.append("blockers:")
        for item in analysis.blockers:
            lines.append(f"  - {item}")
    if execution:
        lines.append("execution:")
        for key, value in execution.items():
            lines.append(f"  - {key}: {value}")
    print("\n".join(lines))


def main() -> int:
    args = parse_args()
    skill_dir = Path(__file__).resolve().parent.parent
    try:
        analysis = build_analysis(args, skill_dir)
        execution: dict[str, Any] | None = None
        if args.mode == "execute":
            if analysis.blockers:
                if args.json:
                    print(json.dumps(analysis_to_jsonable(analysis), ensure_ascii=False, indent=2))
                else:
                    print_text_report(analysis)
                return 2
            execution = execute_plan(Path(args.repo).resolve(), analysis, sync_target=args.sync_target)

        if args.json:
            payload = analysis_to_jsonable(analysis)
            if execution:
                payload["execution"] = execution
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print_text_report(analysis, execution=execution)
        return 0
    except (GitCommandError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
