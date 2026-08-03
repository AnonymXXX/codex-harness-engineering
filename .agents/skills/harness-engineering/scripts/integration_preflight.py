#!/usr/bin/env python3
"""Classify the safe next step for integrating a local task branch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Sequence


ACTIONS = {
    "ALREADY_INTEGRATED",
    "DIRECT_FF",
    "REBASE_THEN_FF",
    "MR_REQUIRED",
    "STOP",
}


class PreflightError(RuntimeError):
    pass


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
    )


def _git_stdout(root: Path, *args: str) -> str:
    result = _git(root, *args)
    if result.returncode != 0:
        raise PreflightError(f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _worktree_root(target: Path) -> Path:
    if not target.is_dir():
        raise PreflightError(f"worktree is not a directory: {target}")
    result = _git(target, "rev-parse", "--show-toplevel", "--is-inside-work-tree")
    lines = result.stdout.splitlines()
    if result.returncode != 0 or len(lines) < 2 or lines[-1].strip() != "true":
        raise PreflightError(f"not a Git worktree: {target}")
    return Path(lines[0]).resolve()


def _commit_oid(root: Path, ref: str) -> str:
    result = _git(root, "rev-parse", "--verify", f"{ref}^{{commit}}")
    if result.returncode != 0:
        raise PreflightError(f"missing commit ref: {ref}")
    return result.stdout.strip()


def _is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    result = _git(root, "merge-base", "--is-ancestor", ancestor, descendant)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise PreflightError("could not compare commit ancestry")


def _has_common_history(root: Path, left: str, right: str) -> bool:
    result = _git(root, "merge-base", left, right)
    if result.returncode == 0:
        return bool(result.stdout.strip())
    if result.returncode == 1:
        return False
    raise PreflightError("could not inspect commit history")


def _task_is_shared(root: Path, remote: str, task: str) -> bool:
    result = _git(
        root,
        "ls-remote",
        "--exit-code",
        "--heads",
        remote,
        f"refs/heads/{task}",
    )
    if result.returncode == 0:
        return True
    if result.returncode == 2:
        return False
    raise PreflightError("could not inspect remote task branch")


def _commits_not_in(root: Path, include: str, exclude: str) -> list[dict[str, str]]:
    output = _git_stdout(
        root,
        "log",
        "--format=%H%x00%s",
        f"{exclude}..{include}",
    )
    commits: list[dict[str, str]] = []
    for line in output.splitlines():
        oid, separator, subject = line.partition("\0")
        if not separator:
            raise PreflightError("could not parse task baseline commits")
        commits.append({"oid": oid, "subject": subject})
    return commits


def _result(
    *,
    action: str,
    reason: str,
    repo: Path | None,
    remote: str,
    task: str,
    target: str,
    task_oid: str | None = None,
    target_oid: str | None = None,
    task_base_oid: str | None = None,
    baseline_checked: bool = False,
    extra_commits: list[dict[str, str]] | None = None,
    task_shared: bool | None = None,
    fetched: bool = False,
) -> dict[str, Any]:
    if action not in ACTIONS:
        raise ValueError(f"unknown action: {action}")
    return {
        "action": action,
        "reason": reason,
        "repo": str(repo) if repo else None,
        "remote": remote,
        "task_ref": f"refs/heads/{task}",
        "task_oid": task_oid,
        "target_ref": f"refs/remotes/{remote}/{target}",
        "target_oid": target_oid,
        "task_base_oid": task_base_oid,
        "baseline_checked": baseline_checked,
        "extra_commits": extra_commits or [],
        "task_shared": task_shared,
        "fetched": fetched,
    }


def preflight(
    worktree: Path,
    *,
    task: str,
    task_base: str,
    target: str,
    remote: str,
    integration_mode: str,
    fetch: bool,
) -> dict[str, Any]:
    root: Path | None = None
    fetched = False
    task_oid: str | None = None
    target_oid: str | None = None
    task_base_oid: str | None = None
    baseline_checked = False
    extra_commits: list[dict[str, str]] = []
    task_shared: bool | None = None
    try:
        root = _worktree_root(worktree.expanduser())
        current_branch = _git_stdout(root, "symbolic-ref", "--quiet", "--short", "HEAD")
        if current_branch != task:
            raise PreflightError(
                f"task worktree is on {current_branch}, expected local task branch {task}"
            )
        task_ref = f"refs/heads/{task}"
        task_oid = _commit_oid(root, task_ref)
        if _git_stdout(root, "status", "--porcelain"):
            raise PreflightError("task worktree is not clean")
        task_base_oid = _commit_oid(root, task_base)
        baseline_checked = True
        if not _is_ancestor(root, task_base_oid, task_oid):
            raise PreflightError("task base is not an ancestor of the task branch")

        target_ref = f"refs/remotes/{remote}/{target}"
        if fetch:
            fetch_result = _git(root, "fetch", "--prune", remote, target)
            if fetch_result.returncode != 0:
                raise PreflightError(f"could not fetch {remote}/{target}")
            fetched = True
        target_oid = _commit_oid(root, target_ref)
        if not _has_common_history(root, task_base_oid, target_oid):
            raise PreflightError("task base and target have unrelated histories")
        extra_commits = _commits_not_in(root, task_base_oid, target_oid)
        if extra_commits:
            raise PreflightError(
                f"task base contains {len(extra_commits)} commit(s) not published to "
                f"{remote}/{target}"
            )
        direct_target = task == target
        task_shared = False if direct_target else _task_is_shared(root, remote, task)

        if _is_ancestor(root, task_oid, target_oid):
            return _result(
                action="ALREADY_INTEGRATED",
                reason=f"task commit is already contained in {remote}/{target}",
                repo=root,
                remote=remote,
                task=task,
                target=target,
                task_oid=task_oid,
                target_oid=target_oid,
                task_base_oid=task_base_oid,
                baseline_checked=baseline_checked,
                extra_commits=extra_commits,
                task_shared=task_shared,
                fetched=fetched,
            )
        target_is_task_ancestor = _is_ancestor(root, target_oid, task_oid)
        if direct_target and not target_is_task_ancestor:
            raise PreflightError(
                "direct target branch has diverged from the remote target"
            )
        if integration_mode == "mr-required" or task_shared:
            reason = (
                "project policy requires a merge request"
                if integration_mode == "mr-required"
                else "task branch is already shared on the remote"
            )
            return _result(
                action="MR_REQUIRED",
                reason=reason,
                repo=root,
                remote=remote,
                task=task,
                target=target,
                task_oid=task_oid,
                target_oid=target_oid,
                task_base_oid=task_base_oid,
                baseline_checked=baseline_checked,
                extra_commits=extra_commits,
                task_shared=task_shared,
                fetched=fetched,
            )
        if target_is_task_ancestor:
            return _result(
                action="DIRECT_FF",
                reason=f"{remote}/{target} can fast-forward to the task commit",
                repo=root,
                remote=remote,
                task=task,
                target=target,
                task_oid=task_oid,
                target_oid=target_oid,
                task_base_oid=task_base_oid,
                baseline_checked=baseline_checked,
                extra_commits=extra_commits,
                task_shared=task_shared,
                fetched=fetched,
            )

        return _result(
            action="REBASE_THEN_FF",
            reason="current task commits must be rebased onto the remote target",
            repo=root,
            remote=remote,
            task=task,
            target=target,
            task_oid=task_oid,
            target_oid=target_oid,
            task_base_oid=task_base_oid,
            baseline_checked=baseline_checked,
            extra_commits=extra_commits,
            task_shared=task_shared,
            fetched=fetched,
        )
    except PreflightError as exc:
        return _result(
            action="STOP",
            reason=str(exc),
            repo=root,
            remote=remote,
            task=task,
            target=target,
            task_oid=task_oid,
            target_oid=target_oid,
            task_base_oid=task_base_oid,
            baseline_checked=baseline_checked,
            extra_commits=extra_commits,
            task_shared=task_shared,
            fetched=fetched,
        )


def _print_human(result: dict[str, Any]) -> None:
    print(f"Integration preflight: {result['action']}")
    print(f"Reason: {result['reason']}")
    print(f"Task: {result['task_ref']} @ {result['task_oid'] or 'unknown'}")
    print(f"Target: {result['target_ref']} @ {result['target_oid'] or 'unknown'}")
    print(f"Task base: {result['task_base_oid'] or 'unknown'}")
    print(f"Baseline checked: {str(result['baseline_checked']).lower()}")
    for commit in result["extra_commits"]:
        print(f"Extra commit: {commit['oid']} {commit['subject']}")
    shared = result["task_shared"]
    print(f"Task shared: {'unknown' if shared is None else str(shared).lower()}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("worktree", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--task", required=True, help="Local task branch name")
    parser.add_argument(
        "--task-base",
        required=True,
        help="Target branch commit recorded before the task worktree was created",
    )
    parser.add_argument("--target", required=True, help="Remote target branch name")
    parser.add_argument("--remote", default="origin")
    parser.add_argument(
        "--integration-mode",
        choices=("auto", "mr-required"),
        default="auto",
    )
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--format", choices=("human", "json"), default="human")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = preflight(
        args.worktree,
        task=args.task,
        task_base=args.task_base,
        target=args.target,
        remote=args.remote,
        integration_mode=args.integration_mode,
        fetch=not args.no_fetch,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    else:
        _print_human(result)
    return 2 if result["action"] == "STOP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
