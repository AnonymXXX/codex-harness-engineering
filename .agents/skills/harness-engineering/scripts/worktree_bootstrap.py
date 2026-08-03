#!/usr/bin/env python3
"""Prepare a Git worktree with a project hook or a frozen package install."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Sequence


PACKAGE_MANAGERS = {
    "pnpm": (("pnpm-lock.yaml",), ("pnpm", "install", "--frozen-lockfile")),
    "npm": (("package-lock.json",), ("npm", "ci")),
    "yarn": (("yarn.lock",), ("yarn", "install", "--immutable")),
    "bun": (("bun.lock", "bun.lockb"), ("bun", "install", "--frozen-lockfile")),
}


class BootstrapError(RuntimeError):
    pass


def _git_worktree_root(target: Path) -> Path:
    if not target.is_dir():
        raise BootstrapError(f"target is not a directory: {target}")
    result = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--show-toplevel", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
    )
    lines = result.stdout.splitlines()
    if result.returncode != 0 or len(lines) < 2 or lines[-1].strip() != "true":
        raise BootstrapError(f"target is not a Git worktree: {target}")
    return Path(lines[0]).resolve()


def _declared_package_manager(root: Path) -> str | None:
    package_json = root / "package.json"
    if not package_json.is_file():
        return None
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BootstrapError(f"cannot read package.json: {exc}") from exc
    value = data.get("packageManager") if isinstance(data, dict) else None
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise BootstrapError("package.json packageManager must be a non-empty string")
    manager = value.split("@", 1)[0].strip()
    if manager not in PACKAGE_MANAGERS:
        raise BootstrapError(f"unsupported packageManager: {value}")
    return manager


def _manager_for_lockfiles(root: Path) -> str | None:
    present = {
        manager
        for manager, (lockfiles, _) in PACKAGE_MANAGERS.items()
        if any((root / lockfile).is_file() for lockfile in lockfiles)
    }
    if len(present) > 1:
        names = ", ".join(sorted(present))
        raise BootstrapError(f"multiple package managers are present ({names}); declare packageManager")
    return next(iter(present), None)


def _install_command(root: Path) -> tuple[str, ...] | None:
    declared = _declared_package_manager(root)
    if declared:
        lockfiles, command = PACKAGE_MANAGERS[declared]
        if not any((root / lockfile).is_file() for lockfile in lockfiles):
            expected = " or ".join(lockfiles)
            raise BootstrapError(f"packageManager {declared} requires {expected}")
        return command

    detected = _manager_for_lockfiles(root)
    if detected:
        return PACKAGE_MANAGERS[detected][1]
    if (root / "package.json").is_file():
        raise BootstrapError("package.json has no packageManager or supported lockfile")
    return None


def bootstrap(target: Path, *, dry_run: bool) -> int:
    root = _git_worktree_root(target.expanduser())
    hook = root / "scripts" / "bootstrap-worktree.sh"
    if hook.exists():
        if not hook.is_file() or not (hook.stat().st_mode & 0o111):
            raise BootstrapError(f"project bootstrap hook is not executable: {hook}")
        command = (str(hook),)
        label = "scripts/bootstrap-worktree.sh"
    else:
        command = _install_command(root)
        if command is None:
            print(f"Bootstrap: no bootstrap action needed for {root}")
            return 0
        label = shlex.join(command)

    prefix = "Bootstrap dry-run" if dry_run else "Bootstrap"
    print(f"{prefix}: {label}")
    if dry_run:
        return 0
    try:
        return subprocess.run(command, cwd=root).returncode
    except OSError as exc:
        raise BootstrapError(f"could not run {label}: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("worktree", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return bootstrap(args.worktree, dry_run=args.dry_run)
    except BootstrapError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
