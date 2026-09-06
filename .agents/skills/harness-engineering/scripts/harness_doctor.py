#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6,<7"]
# ///
"""Health checks, safe worktree cleanup, and deterministic Harness indexing."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Sequence
from urllib.parse import unquote, urlsplit

import yaml

try:
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.9
    try:
        import tomli as tomllib  # type: ignore[import-not-found,no-redef]
    except ModuleNotFoundError:  # pragma: no cover - optional dependency
        tomllib = None  # type: ignore[assignment]

REPORT_VERSION = 10
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_PATTERN = re.compile(r"^---\n(.*?)\n---(?:\n|$)", re.DOTALL)
HARNESS_SKILLS = {
    "codebase-design",
    "diagnosing-bugs",
    "domain-modeling",
    "harness-engineering",
    "tdd",
}
HARNESS_INVOCATION_POLICY = {
    "harness-engineering": True,
}
WORKTREE_DEBT_STATES = {
    "dirty",
    "clean-unmerged-or-rewritten",
    "detached",
    "missing-prunable",
}
SKIP_SCAN_DIRS = {
    ".cache",
    ".git",
    ".idea",
    ".next",
    ".nuxt",
    ".output",
    ".turbo",
    ".venv",
    ".vscode",
    "build",
    "dist",
    "node_modules",
    "target",
    "vendor",
}
MARKDOWN_LINK_PATTERN = re.compile(
    r"!?\[[^\]\n]*\]\(\s*(?P<target><[^>\n]+>|[^\s)]+)",
)
MARKDOWN_REFERENCE_PATTERN = re.compile(
    r"^\s*\[[^\]\n]+\]:\s*(?P<target><[^>\n]+>|\S+)",
    re.MULTILINE,
)
OPEN_CHECKBOX_PATTERN = re.compile(r"^\s*[-*+]\s+\[ \]", re.MULTILINE)
VERIFICATION_HEADING_PATTERN = re.compile(r"^##\s+Verification\s*$", re.MULTILINE)
VERIFICATION_FIELD_PATTERN = re.compile(
    r"^\s*[-*+]\s+(Mode|Command|Reason):\s*(.*?)\s*$",
    re.MULTILINE | re.IGNORECASE,
)
MEMORY_LINE_LIMITS = {"memory_summary.md": 300, "MEMORY.md": 1000}


def check(
    severity: str,
    code: str,
    message: str,
    *,
    section: str = "skills",
    **details: Any,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "severity": severity,
        "code": code,
        "message": message,
        "section": section,
    }
    if details:
        item["details"] = details
    return item




def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _frontmatter(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8")
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        raise ValueError("missing or malformed YAML frontmatter")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a mapping")
    return data


def _normalize_description(value: str) -> str:
    return " ".join(value.split())


def discover_skills(skills_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    skills: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    if not skills_root.is_dir():
        return [], [
            check("error", "skills-root-missing", f"Skills root does not exist: {skills_root}")
        ]

    for skill_dir in sorted(
        (path for path in skills_root.iterdir() if path.is_dir()),
        key=lambda path: path.name,
    ):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            checks.append(
                check(
                    "warning",
                    "skill-directory-ignored",
                    f"Directory has no SKILL.md and was ignored: {skill_dir}",
                    path=str(skill_dir),
                )
            )
            continue

        try:
            metadata = _frontmatter(skill_md)
        except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
            checks.append(
                check(
                    "error",
                    "skill-frontmatter-invalid",
                    f"Invalid SKILL.md frontmatter in {skill_dir.name}: {exc}",
                    path=str(skill_md),
                )
            )
            continue

        name = metadata.get("name")
        description = metadata.get("description")
        invalid = False
        if not isinstance(name, str) or not name.strip():
            checks.append(
                check(
                    "error",
                    "skill-name-invalid",
                    f"Skill has no valid name: {skill_md}",
                    path=str(skill_md),
                )
            )
            invalid = True
        else:
            name = name.strip()
            if name != skill_dir.name:
                checks.append(
                    check(
                        "error",
                        "skill-name-mismatch",
                        f"Skill name {name!r} does not match directory {skill_dir.name!r}",
                        path=str(skill_md),
                    )
                )
                invalid = True
            if len(name) > 64 or not SKILL_NAME_PATTERN.fullmatch(name):
                checks.append(
                    check(
                        "error",
                        "skill-name-format",
                        f"Skill name is not valid hyphen-case: {name!r}",
                        path=str(skill_md),
                    )
                )
                invalid = True

        if not isinstance(description, str) or not description.strip():
            checks.append(
                check(
                    "error",
                    "skill-description-invalid",
                    f"Skill has no valid description: {skill_md}",
                    path=str(skill_md),
                )
            )
            invalid = True
        else:
            description = _normalize_description(description)
            if len(description) > 1024:
                checks.append(
                    check(
                        "error",
                        "skill-description-too-long",
                        f"Skill description exceeds 1024 characters: {skill_dir.name}",
                        path=str(skill_md),
                    )
                )
                invalid = True

        if invalid:
            continue

        openai_yaml = skill_dir / "agents" / "openai.yaml"
        openai_data: dict[str, Any] | None = None
        if name in HARNESS_SKILLS:
            # Marketplace-style metadata is required only for Harness-owned skills,
            # where it drives invocation policy. Local user skills may omit it.
            if not openai_yaml.is_file():
                checks.append(
                    check(
                        "error",
                        "skill-openai-metadata-missing",
                        f"Skill has no agents/openai.yaml: {name}",
                        path=str(openai_yaml),
                    )
                )
            else:
                try:
                    loaded = _load_yaml(openai_yaml)
                    if not isinstance(loaded, dict):
                        raise ValueError("metadata must be a mapping")
                    openai_data = loaded
                    interface = loaded.get("interface")
                    if not isinstance(interface, dict):
                        raise ValueError("interface must be a mapping")
                    default_prompt = interface.get("default_prompt")
                    if not isinstance(default_prompt, str) or f"${name}" not in default_prompt:
                        raise ValueError(f"interface.default_prompt must mention ${name}")
                    short_description = interface.get("short_description")
                    if not isinstance(short_description, str) or not 25 <= len(short_description) <= 64:
                        raise ValueError(
                            "interface.short_description must contain 25 to 64 characters"
                        )
                except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
                    checks.append(
                        check(
                            "error",
                            "skill-openai-metadata-invalid",
                            f"Invalid agents/openai.yaml for {name}: {exc}",
                            path=str(openai_yaml),
                        )
                    )
        elif openai_yaml.is_file():
            try:
                loaded = _load_yaml(openai_yaml)
                if isinstance(loaded, dict):
                    openai_data = loaded
            except (OSError, UnicodeError, ValueError, yaml.YAMLError):
                openai_data = None

        skills.append(
            {
                "name": name,
                "description": description,
                "path": str(skill_dir),
                "openai": openai_data,
            }
        )

    return skills, checks


def _display_path(path: Path) -> str:
    try:
        return f"~/{path.resolve().relative_to(Path.home().resolve())}"
    except (OSError, ValueError):
        return str(path.resolve())


def render_skill_index(skills: Sequence[dict[str, Any]], skills_root: Path) -> str:
    lines = [
        "# 跨 Agent Skills 索引",
        "",
        f"目标目录：`{_display_path(skills_root)}`",
        "",
        f"有效 Skills 数量：{len(skills)}",
        "",
        "## 有效 Skills",
        "",
    ]
    for skill in sorted(skills, key=lambda item: item["name"]):
        lines.extend(
            [
                f"- **{skill['name']}**",
                f"  - `description`: {skill['description']}",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _has_errors(checks: Iterable[dict[str, Any]]) -> bool:
    return any(item["severity"] == "error" for item in checks)


def update_skill_index(
    skills_root: Path,
    index_path: Path,
    *,
    write: bool,
) -> dict[str, Any]:
    skills, checks = discover_skills(skills_root)
    if _has_errors(checks):
        return {
            "exit_code": 1,
            "changed": False,
            "checks": checks,
            "content": None,
        }

    content = render_skill_index(skills, skills_root)
    try:
        current = index_path.read_text(encoding="utf-8") if index_path.exists() else None
    except (OSError, UnicodeError) as exc:
        checks.append(
            check("error", "skill-index-read-failed", f"Cannot read {index_path}: {exc}")
        )
        return {
            "exit_code": 1,
            "changed": False,
            "checks": checks,
            "content": content,
        }

    changed = current != content
    if write and changed:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        temp_name: str | None = None
        target_mode = index_path.stat().st_mode & 0o777 if index_path.exists() else 0o644
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=index_path.parent,
                prefix=f".{index_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temp_name = handle.name
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_name, target_mode)
            os.replace(temp_name, index_path)
        except OSError as exc:
            if temp_name:
                Path(temp_name).unlink(missing_ok=True)
            checks.append(
                check("error", "skill-index-write-failed", f"Cannot write {index_path}: {exc}")
            )
            return {
                "exit_code": 1,
                "changed": False,
                "checks": checks,
                "content": content,
            }

    exit_code = 0 if write or not changed else 1
    return {
        "exit_code": exit_code,
        "changed": changed,
        "checks": checks,
        "content": content,
    }


def _run_git(repo: Path, *args: str, check_result: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    if check_result and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "git command failed")
    return result


def _discover_repositories(repo_roots: Sequence[Path]) -> tuple[list[Path], list[dict[str, Any]]]:
    repositories: dict[str, Path] = {}
    checks: list[dict[str, Any]] = []
    for root in repo_roots:
        root = root.expanduser()
        if not root.exists():
            checks.append(
                check(
                    "warning",
                    "repo-root-missing",
                    f"Repository root does not exist and was skipped: {root}",
                    section="worktrees",
                    path=str(root),
                )
            )
            continue
        for current, dirnames, filenames in os.walk(root):
            has_git = ".git" in dirnames or ".git" in filenames
            dirnames[:] = [name for name in dirnames if name not in SKIP_SCAN_DIRS]
            if not has_git:
                continue
            repo = Path(current)
            result = _run_git(
                repo,
                "rev-parse",
                "--path-format=absolute",
                "--git-common-dir",
                check_result=False,
            )
            if result.returncode == 0:
                worktree_listing = _run_git(
                    repo,
                    "worktree",
                    "list",
                    "--porcelain",
                    check_result=False,
                )
                parsed = (
                    _parse_worktree_porcelain(worktree_listing.stdout)
                    if worktree_listing.returncode == 0
                    else []
                )
                primary = Path(parsed[0]["path"]).resolve() if parsed else repo.resolve()
                repositories.setdefault(os.path.realpath(result.stdout.strip()), primary)
    return sorted(repositories.values(), key=str), checks


def _parse_worktree_porcelain(output: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in output.splitlines():
        if not line:
            if current:
                records.append(current)
                current = None
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            if current:
                records.append(current)
            current = {"path": value}
        elif current is not None:
            if key in {"bare", "detached", "locked", "prunable"}:
                current[key] = value or True
            else:
                current[key] = value
    if current:
        records.append(current)
    return records


def _ledger_candidates(repo: Path) -> list[Path]:
    return [
        repo / "docs" / "exec-plans" / "worktree-ledger.md",
        repo / "docs" / "worktree-ledger.md",
    ]


def _ledger_coverage(repo: Path, path: str, branch: str | None) -> tuple[bool, str | None]:
    aliases = {path, os.path.realpath(path)}
    aliases.update(
        item.removeprefix("/private")
        for item in tuple(aliases)
        if item.startswith("/private/")
    )
    needles = sorted(aliases)
    if branch:
        needles.extend([branch, branch.removeprefix("refs/heads/")])
    for candidate in _ledger_candidates(repo):
        if not candidate.is_file():
            continue
        try:
            content = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if any(needle and needle in content for needle in needles):
            return True, str(candidate)
    return False, None


def _worktree_state(repo: Path, item: dict[str, Any], integration_branch: str) -> str:
    path = Path(item["path"])
    if not path.exists():
        return "missing-prunable"
    status = _run_git(path, "status", "--porcelain", check_result=False)
    if status.returncode != 0 or status.stdout.strip():
        return "dirty"
    if item.get("detached"):
        return "detached"
    branch = item.get("branch")
    if not branch:
        return "detached"
    merged = _run_git(
        repo,
        "merge-base",
        "--is-ancestor",
        branch,
        integration_branch,
        check_result=False,
    )
    return "clean-ancestor" if merged.returncode == 0 else "clean-unmerged-or-rewritten"


def _parse_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None


def _worktree_last_activity(repo: Path, item: dict[str, Any]) -> datetime | None:
    candidates: list[datetime] = []
    path = Path(item["path"])
    if path.exists():
        try:
            stat = path.stat()
            created = getattr(stat, "st_birthtime", stat.st_ctime)
            candidates.extend(
                [
                    datetime.fromtimestamp(created).astimezone(),
                    datetime.fromtimestamp(stat.st_mtime).astimezone(),
                ]
            )
        except OSError:
            pass
    branch = item.get("branch")
    if branch:
        result = _run_git(
            repo,
            "show",
            "-s",
            "--format=%cI",
            branch,
            check_result=False,
        )
        if result.returncode == 0:
            committed = _parse_datetime(result.stdout.strip())
            if committed:
                candidates.append(committed)
    return max(candidates) if candidates else None


def _worktree_age(
    repo: Path,
    item: dict[str, Any],
    now: datetime,
) -> tuple[datetime | None, float | None, str]:
    last_activity = _worktree_last_activity(repo, item)
    if not last_activity:
        return None, None, "unknown"
    age_days = max(0.0, (now - last_activity).total_seconds() / 86400)
    if age_days < 1:
        lifecycle = "active"
    elif age_days <= 7:
        lifecycle = "recent"
    else:
        lifecycle = "stale"
    return last_activity, age_days, lifecycle


def scan_worktrees(
    repo_roots: Sequence[Path],
    *,
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    now = now or datetime.now().astimezone()
    repositories, checks = _discover_repositories(repo_roots)
    records: list[dict[str, Any]] = []
    for repo in repositories:
        listing = _run_git(repo, "worktree", "list", "--porcelain", check_result=False)
        if listing.returncode != 0:
            checks.append(
                check(
                    "warning",
                    "worktree-list-failed",
                    f"Cannot inspect worktrees for {repo}: {listing.stderr.strip()}",
                    section="worktrees",
                    repo=str(repo),
                )
            )
            continue
        worktrees = _parse_worktree_porcelain(listing.stdout)
        if len(worktrees) <= 1:
            continue
        integration = worktrees[0]
        integration_branch = integration.get("branch") or integration.get("HEAD")
        for item in worktrees[1:]:
            state = _worktree_state(repo, item, integration_branch)
            branch = item.get("branch")
            covered, ledger_path = _ledger_coverage(repo, item["path"], branch)
            last_activity, age_days, lifecycle = _worktree_age(repo, item, now)
            record = {
                "repo": str(repo),
                "path": item["path"],
                "branch": branch.removeprefix("refs/heads/") if branch else None,
                "state": state,
                "ledger_covered": covered,
                "ledger_path": ledger_path,
                "locked": bool(item.get("locked")),
                "last_activity_at": last_activity.isoformat() if last_activity else None,
                "age_days": round(age_days, 3) if age_days is not None else None,
                "lifecycle": lifecycle,
            }
            records.append(record)
            if lifecycle == "stale" and state == "clean-ancestor":
                checks.append(
                    check(
                        "warning",
                        "worktree-stale-cleanup-eligible",
                        f"Stale merged worktree may be eligible for safe cleanup: {item['path']}",
                        section="worktrees",
                        **record,
                    )
                )
            elif (
                state in WORKTREE_DEBT_STATES
                and not covered
                and lifecycle != "active"
            ):
                code = (
                    "worktree-stale-needs-attention"
                    if lifecycle == "stale"
                    else "worktree-ledger-missing"
                )
                checks.append(
                    check(
                        "warning",
                        code,
                        f"Cross-session worktree has no discoverable ledger entry: {item['path']}",
                        section="worktrees",
                        **record,
                    )
                )
    return sorted(records, key=lambda item: (item["repo"], item["path"])), checks


def _document_repository(path: Path) -> tuple[Path, str] | None:
    top_level = _run_git(
        path,
        "rev-parse",
        "--show-toplevel",
        check_result=False,
    )
    common_dir = _run_git(
        path,
        "rev-parse",
        "--path-format=absolute",
        "--git-common-dir",
        check_result=False,
    )
    if top_level.returncode != 0 or common_dir.returncode != 0:
        return None
    return Path(top_level.stdout.strip()).resolve(), os.path.realpath(common_dir.stdout.strip())


def _discover_document_repositories(
    repo_roots: Sequence[Path],
) -> tuple[list[Path], list[dict[str, Any]]]:
    repositories: dict[str, Path] = {}
    checks: list[dict[str, Any]] = []
    for raw_root in repo_roots:
        root = raw_root.expanduser()
        if not root.exists():
            checks.append(
                check(
                    "warning",
                    "docs-repo-root-missing",
                    f"Repository root does not exist and was skipped: {root}",
                    section="docs",
                    path=str(root),
                )
            )
            continue

        explicit = _document_repository(root)
        if explicit:
            repo, common_dir = explicit
            repositories.setdefault(common_dir, repo)
            continue

        for current, dirnames, filenames in os.walk(root):
            has_git = ".git" in dirnames or ".git" in filenames
            dirnames[:] = [name for name in dirnames if name not in SKIP_SCAN_DIRS]
            if not has_git:
                continue
            discovered = _document_repository(Path(current))
            if discovered:
                repo, common_dir = discovered
                repositories.setdefault(common_dir, repo)
    return sorted(repositories.values(), key=str), checks


def _tracked_markdown_files(repo: Path) -> list[Path]:
    result = _run_git(
        repo,
        "ls-files",
        "-z",
        "--",
        "*.md",
        "*.markdown",
        check_result=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"Cannot list tracked Markdown files: {repo}")
    return [repo / item for item in result.stdout.split("\0") if item]


def _without_fenced_code(content: str) -> str:
    lines: list[str] = []
    fence: str | None = None
    for line in content.splitlines(keepends=True):
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)[0]
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            lines.append("\n" if line.endswith("\n") else "")
        elif fence is None:
            lines.append(line)
        else:
            lines.append("\n" if line.endswith("\n") else "")
    return "".join(lines)


def _local_link_target(repo: Path, source: Path, target: str) -> Path | None:
    target = target.strip().strip("<>")
    if not target or target.startswith("#") or target.startswith("//"):
        return None
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None
    local_path = unquote(parsed.path)
    if not local_path:
        return None
    if local_path.startswith("/"):
        return repo / local_path.lstrip("/")
    return source.parent / local_path


def _document_age_days(repo: Path, path: Path, now: datetime) -> float | None:
    relative = path.relative_to(repo)
    result = _run_git(
        repo,
        "log",
        "-1",
        "--format=%cI",
        "--",
        str(relative),
        check_result=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    committed = _parse_datetime(result.stdout.strip())
    if committed is None:
        return None
    return max(0.0, (now - committed).total_seconds() / 86400)


def _meaningful_value(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip().strip("`").strip()
    if not normalized:
        return False
    lowered = normalized.lower()
    return lowered not in {
        "n/a",
        "na",
        "none",
        "not applicable",
        "<deterministic command>",
        "<deterministic local command, or explain why no mechanical check exists>",
        "<manual/not-applicable 时必填>",
    } and not (normalized.startswith("<") and normalized.endswith(">"))


def _verification_issue(content: str) -> str | None:
    heading = VERIFICATION_HEADING_PATTERN.search(content)
    if not heading:
        return "missing Verification section"
    remainder = content[heading.end():]
    next_heading = re.search(r"^##\s+", remainder, re.MULTILINE)
    section = remainder[: next_heading.start()] if next_heading else remainder
    fields = {
        match.group(1).lower(): match.group(2).strip()
        for match in VERIFICATION_FIELD_PATTERN.finditer(section)
    }
    if fields:
        mode = fields.get("mode", "").lower()
        if mode not in {"automated", "manual", "not-applicable"}:
            return "Mode must be automated, manual, or not-applicable"
        if "command" not in fields:
            return "Command field is required"
        if mode == "automated" and not _meaningful_value(fields.get("command")):
            return "automated verification requires a deterministic Command"
        if mode in {"manual", "not-applicable"} and not _meaningful_value(
            fields.get("reason")
        ):
            return f"{mode} verification requires a Reason"
        return None

    fenced = re.search(r"```(?:bash|sh|shell|zsh)?\s*\n(.*?)```", section, re.DOTALL)
    if fenced and _meaningful_value(fenced.group(1)):
        return None
    return "Verification must use Mode/Command/Reason fields or a legacy command fence"


def _memory_audit(memory_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    audit: dict[str, Any] = {}
    checks: list[dict[str, Any]] = []
    for name, limit in MEMORY_LINE_LIMITS.items():
        path = memory_root / name
        if not path.is_file():
            continue
        try:
            lines = len(path.read_text(encoding="utf-8").splitlines())
        except (OSError, UnicodeError) as exc:
            checks.append(
                check(
                    "warning",
                    "docs-memory-read-failed",
                    f"Cannot read Codex memory file {path}: {exc}",
                    section="docs",
                    path=str(path),
                )
            )
            continue
        audit[name] = {"path": str(path), "lines": lines, "limit": limit}
        if lines > limit:
            checks.append(
                check(
                    "warning",
                    "docs-memory-large",
                    f"Codex memory file exceeds {limit} lines: {path} ({lines})",
                    section="docs",
                    path=str(path),
                    lines=lines,
                    limit=limit,
                )
            )
    return audit, checks


def scan_documents(
    repo_roots: Sequence[Path],
    *,
    memory_root: Path,
    now: datetime | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    now = now or datetime.now().astimezone()
    repositories, checks = _discover_document_repositories(repo_roots)
    audit: dict[str, Any] = {
        "repositories": len(repositories),
        "repository_paths": [str(path) for path in repositories],
        "markdown_files": 0,
        "local_links": 0,
        "broken_local_links": 0,
        "large_agents_files": 0,
        "stale_open_plans": 0,
        "engineering_rules": 0,
        "rules_needing_verification": 0,
        "memory": {},
    }

    for repo in repositories:
        try:
            markdown_files = _tracked_markdown_files(repo)
        except RuntimeError as exc:
            checks.append(
                check(
                    "warning",
                    "docs-list-failed",
                    str(exc),
                    section="docs",
                    repo=str(repo),
                )
            )
            continue
        audit["markdown_files"] += len(markdown_files)
        for path in markdown_files:
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                checks.append(
                    check(
                        "warning",
                        "docs-read-failed",
                        f"Cannot read tracked Markdown file {path}: {exc}",
                        section="docs",
                        path=str(path),
                        repo=str(repo),
                    )
                )
                continue
            relative = path.relative_to(repo).as_posix()
            searchable = _without_fenced_code(content)

            for pattern in (MARKDOWN_LINK_PATTERN, MARKDOWN_REFERENCE_PATTERN):
                for match in pattern.finditer(searchable):
                    target_text = match.group("target")
                    target = _local_link_target(repo, path, target_text)
                    if target is None:
                        continue
                    audit["local_links"] += 1
                    if target.exists():
                        continue
                    audit["broken_local_links"] += 1
                    line = searchable.count("\n", 0, match.start()) + 1
                    checks.append(
                        check(
                            "warning",
                            "docs-local-link-missing",
                            f"Missing local link target in {path}:{line}: {target_text}",
                            section="docs",
                            repo=str(repo),
                            path=str(path),
                            line=line,
                            target=target_text,
                        )
                    )

            if path.name == "AGENTS.md":
                line_count = len(content.splitlines())
                if line_count > 120:
                    audit["large_agents_files"] += 1
                    checks.append(
                        check(
                            "warning",
                            "docs-agents-too-long",
                            f"AGENTS.md exceeds 120 lines: {path} ({line_count})",
                            section="docs",
                            repo=str(repo),
                            path=str(path),
                            lines=line_count,
                        )
                    )

            if relative.startswith("docs/exec-plans/") and OPEN_CHECKBOX_PATTERN.search(
                searchable
            ):
                age_days = _document_age_days(repo, path, now)
                if age_days is not None and age_days > 30:
                    audit["stale_open_plans"] += 1
                    checks.append(
                        check(
                            "warning",
                            "docs-exec-plan-stale-open",
                            f"Execution plan is still open after 30 days: {path}",
                            section="docs",
                            repo=str(repo),
                            path=str(path),
                            age_days=round(age_days, 3),
                        )
                    )

            if relative.startswith("docs/engineering-rules/"):
                audit["engineering_rules"] += 1
                issue = _verification_issue(content)
                if issue:
                    audit["rules_needing_verification"] += 1
                    code = (
                        "docs-rule-verification-missing"
                        if issue == "missing Verification section"
                        else "docs-rule-verification-invalid"
                    )
                    checks.append(
                        check(
                            "warning",
                            code,
                            f"Engineering rule verification is incomplete in {path}: {issue}",
                            section="docs",
                            repo=str(repo),
                            path=str(path),
                        )
                    )

    memory_audit, memory_checks = _memory_audit(memory_root.expanduser())
    audit["memory"] = memory_audit
    checks.extend(memory_checks)
    if not [item for item in checks if item.get("section") == "docs"]:
        checks.append(
            check(
                "ok",
                "docs-healthy",
                "Document gardening checks passed",
                section="docs",
            )
        )
    return audit, checks


def _active_process_cwds() -> set[Path]:
    lsof = shutil.which("lsof")
    if not lsof:
        raise RuntimeError("lsof is unavailable; active worktree detection cannot run safely")
    result = subprocess.run(
        [lsof, "-d", "cwd", "-Fn"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or "lsof could not inspect active process directories"
        )
    paths: set[Path] = set()
    for line in result.stdout.splitlines():
        if line.startswith("n/"):
            paths.add(Path(os.path.realpath(line[1:])))
    return paths


def _path_is_active(path: Path, active_cwds: set[Path]) -> bool:
    target = Path(os.path.realpath(path))
    return any(cwd == target or target in cwd.parents for cwd in active_cwds)


def cleanup_worktrees(
    repo_roots: Sequence[Path],
    *,
    older_than_days: int,
    dry_run: bool,
    now: datetime | None = None,
    active_cwds: set[Path] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    now = now or datetime.now().astimezone()
    repositories, checks = _discover_repositories(repo_roots)
    records: list[dict[str, Any]] = []
    if active_cwds is None:
        try:
            active_cwds = _active_process_cwds()
        except RuntimeError as exc:
            checks.append(
                check(
                    "error",
                    "worktree-active-check-failed",
                    str(exc),
                    section="worktrees",
                )
            )
            active_cwds = set()
            active_check_failed = True
        else:
            active_check_failed = False
    else:
        active_cwds = {Path(os.path.realpath(path)) for path in active_cwds}
        active_check_failed = False

    for repo in repositories:
        listing = _run_git(repo, "worktree", "list", "--porcelain", check_result=False)
        if listing.returncode != 0:
            checks.append(
                check(
                    "error",
                    "worktree-list-failed",
                    f"Cannot inspect worktrees for {repo}: {listing.stderr.strip()}",
                    section="worktrees",
                    repo=str(repo),
                )
            )
            continue
        worktrees = _parse_worktree_porcelain(listing.stdout)
        if not worktrees:
            continue
        integration_branch = worktrees[0].get("branch") or worktrees[0].get("HEAD")
        for item in worktrees[1:]:
            state = _worktree_state(repo, item, integration_branch)
            branch_ref = item.get("branch")
            branch = branch_ref.removeprefix("refs/heads/") if branch_ref else None
            covered, ledger_path = _ledger_coverage(repo, item["path"], branch_ref)
            last_activity, age_days, lifecycle = _worktree_age(repo, item, now)
            path = Path(item["path"])
            record = {
                "repo": str(repo),
                "path": item["path"],
                "branch": branch,
                "state": state,
                "ledger_covered": covered,
                "ledger_path": ledger_path,
                "locked": bool(item.get("locked")),
                "last_activity_at": last_activity.isoformat() if last_activity else None,
                "age_days": round(age_days, 3) if age_days is not None else None,
                "lifecycle": lifecycle,
            }
            if active_check_failed:
                status = "active-check-unavailable"
            elif state != "clean-ancestor":
                status = "unsafe-state"
            elif not branch or not branch.startswith("codex/"):
                status = "non-codex-branch"
            elif covered:
                status = "ledger-covered"
            elif item.get("locked"):
                status = "locked"
            elif age_days is None:
                status = "unknown-age"
            elif age_days <= older_than_days:
                status = "too-recent"
            elif _path_is_active(path, active_cwds):
                status = "active-process"
            elif dry_run:
                status = "would-remove"
            else:
                remove = _run_git(
                    repo,
                    "worktree",
                    "remove",
                    "--",
                    str(path),
                    check_result=False,
                )
                if remove.returncode != 0:
                    status = "remove-failed"
                    checks.append(
                        check(
                            "error",
                            "worktree-remove-failed",
                            f"Could not remove {path}: {remove.stderr.strip()}",
                            section="worktrees",
                            **record,
                        )
                    )
                else:
                    delete_branch = _run_git(
                        repo,
                        "branch",
                        "-d",
                        "--",
                        branch,
                        check_result=False,
                    )
                    if delete_branch.returncode == 0:
                        status = "removed"
                    else:
                        status = "worktree-removed-branch-retained"
                        checks.append(
                            check(
                                "error",
                                "worktree-branch-delete-failed",
                                f"Removed worktree but retained branch {branch}: {delete_branch.stderr.strip()}",
                                section="worktrees",
                                **record,
                            )
                        )
            record["cleanup_status"] = status
            records.append(record)

    return sorted(records, key=lambda item: (item["repo"], item["path"])), checks


def _harness_checks(home: Path, skills: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    skill_by_name = {item["name"]: item for item in skills}
    for name in sorted(HARNESS_SKILLS):
        if name not in skill_by_name:
            checks.append(
                check("error", "harness-skill-missing", f"Required Harness skill is missing: {name}")
            )
    for name, expected_implicit in sorted(HARNESS_INVOCATION_POLICY.items()):
        skill = skill_by_name.get(name)
        if not skill:
            continue
        policy = (skill.get("openai") or {}).get("policy")
        implicit = policy.get("allow_implicit_invocation") if isinstance(policy, dict) else None
        if implicit is not expected_implicit:
            checks.append(
                check(
                    "error",
                    "harness-skill-invocation-policy-mismatch",
                    "Harness skill invocation policy mismatch: "
                    f"{name} must set allow_implicit_invocation: "
                    f"{str(expected_implicit).lower()}",
                    skill=name,
                    expected=expected_implicit,
                    actual=implicit,
                )
            )

    required_paths = [
        home / ".codex" / "AGENTS.md",
        home / ".codex" / "docs" / "workflows" / "harness-engineering.md",
        home / ".codex" / "docs" / "workflows" / "git-worktree.md",
        home / ".codex" / "docs" / "workflows" / "document-gardening.md",
        home
        / ".agents"
        / "skills"
        / "harness-engineering"
        / "scripts"
        / "worktree_bootstrap.py",
        home
        / ".agents"
        / "skills"
        / "harness-engineering"
        / "scripts"
        / "integration_preflight.py",
    ]
    template_root = home / ".agents" / "skills" / "harness-engineering" / "assets" / "project-harness"
    required_paths.extend(
        template_root / name
        for name in (
            "product-spec.md",
            "engineering-rule.md",
            "exec-plan.md",
            "worktree-ledger.md",
        )
    )
    for path in required_paths:
        if not path.is_file():
            checks.append(
                check(
                    "error",
                    "harness-path-missing",
                    f"Required Harness file is missing: {path}",
                    path=str(path),
                )
            )
    return checks


def _runtime_visibility_checks(expected: Sequence[str]) -> list[dict[str, Any]]:
    codex = shutil.which("codex")
    if not codex:
        return [
            check(
                "warning",
                "codex-cli-missing",
                "Codex CLI is unavailable; runtime skill visibility was not checked",
            )
        ]
    result = subprocess.run(
        [codex, "debug", "prompt-input", "Check Harness skill visibility"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return [
            check(
                "warning",
                "codex-prompt-input-failed",
                "Codex could not render prompt input; runtime skill visibility was not checked",
                stderr=result.stderr.strip(),
            )
        ]
    checks: list[dict[str, Any]] = []
    for name in expected:
        if f"- {name}:" not in result.stdout:
            checks.append(
                check(
                    "error",
                    "runtime-skill-missing",
                    f"Skill is not visible in Codex prompt input: {name}",
                    skill=name,
                )
            )
    if not checks:
        checks.append(
            check(
                "ok",
                "runtime-skills-visible",
                f"All {len(expected)} implicitly invocable Harness skills are visible to Codex",
            )
        )
    return checks










def make_report(
    *,
    checks: Sequence[dict[str, Any]],
    worktrees: Sequence[dict[str, Any]],
    docs_audit: dict[str, Any] | None = None,
    scope: str = "full",
    sections: Sequence[str] | None = None,
) -> dict[str, Any]:
    docs_audit = docs_audit or {}
    summary = {
        "errors": sum(item["severity"] == "error" for item in checks),
        "warnings": sum(item["severity"] == "warning" for item in checks),
        "ok": sum(item["severity"] == "ok" for item in checks),
    }
    selected_sections = list(sections or (["skills"] if scope == "core" else [
        "skills",
        "worktrees",
    ]))
    section_summaries: dict[str, dict[str, Any]] = {}
    for section in selected_sections:
        section_checks = [item for item in checks if item.get("section", "skills") == section]
        section_summary: dict[str, Any] = {
            "errors": sum(item["severity"] == "error" for item in section_checks),
            "warnings": sum(item["severity"] == "warning" for item in section_checks),
            "ok": sum(item["severity"] == "ok" for item in section_checks),
        }
        if section == "worktrees":
            section_summary.update(
                {
                    "inspected": len(worktrees),
                    "active": sum(item.get("lifecycle") == "active" for item in worktrees),
                    "recent": sum(item.get("lifecycle") == "recent" for item in worktrees),
                    "stale": sum(item.get("lifecycle") == "stale" for item in worktrees),
                }
            )
        elif section == "docs":
            section_summary.update(docs_audit)
        section_summaries[section] = section_summary
    return {
        "version": REPORT_VERSION,
        "scope": scope,
        "sections": selected_sections,
        "summary": summary,
        "section_summaries": section_summaries,
        "checks": list(checks),
        "worktrees": list(worktrees),
        "docs_audit": docs_audit,
    }

def render_report(report: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    summary = report["summary"]
    lines = [
        f"Harness Doctor ({report.get('scope', 'full')})",
        f"errors={summary['errors']} warnings={summary['warnings']} ok={summary['ok']}",
    ]
    symbols = {"error": "ERROR", "warning": "WARN", "ok": "OK"}
    labels = {
        "skills": "Skills",
        "worktrees": "Worktrees",
        "docs": "Docs",
    }
    for section in report.get("sections", []):
        section_summary = report["section_summaries"][section]
        lines.append(f"[{labels[section]}]")
        section_line = (
            f"errors={section_summary['errors']} "
            f"warnings={section_summary['warnings']} ok={section_summary['ok']}"
        )
        if section == "worktrees":
            section_line += (
                f" inspected={section_summary['inspected']}"
                f" active={section_summary['active']}"
                f" recent={section_summary['recent']}"
                f" stale={section_summary['stale']}"
            )
        elif section == "docs":
            section_line += (
                f" repositories={section_summary.get('repositories', 0)}"
                f" markdown_files={section_summary.get('markdown_files', 0)}"
                f" broken_local_links={section_summary.get('broken_local_links', 0)}"
                f" large_agents_files={section_summary.get('large_agents_files', 0)}"
                f" stale_open_plans={section_summary.get('stale_open_plans', 0)}"
                " rules_needing_verification="
                f"{section_summary.get('rules_needing_verification', 0)}"
            )
        lines.append(section_line)
        for item in report["checks"]:
            if item.get("section", "skills") == section:
                lines.append(
                    f"[{symbols[item['severity']]}] {item['code']}: {item['message']}"
                )
    return "\n".join(lines) + "\n"

def report_exit_code(report: dict[str, Any], *, strict: bool) -> int:
    if report["summary"]["errors"]:
        return 1
    if strict and report["summary"]["warnings"]:
        return 1
    return 0


def _default_repo_roots(home: Path) -> list[Path]:
    current = _run_git(
        Path.cwd(),
        "rev-parse",
        "--show-toplevel",
        check_result=False,
    )
    if current.returncode == 0 and current.stdout.strip():
        return [Path(current.stdout.strip()).resolve()]
    return []


def _doctor_command(args: argparse.Namespace) -> int:
    home = Path.home()
    skills_root = home / ".agents" / "skills"
    index_path = home / ".agents" / "skills-index.md"
    sections = args.section or (["skills", "worktrees"] if args.full else ["skills"])
    checks: list[dict[str, Any]] = []
    if "skills" in sections:
        skills, discovery_checks = discover_skills(skills_root)
        checks.extend(
            discovery_checks
            if args.full
            else [item for item in discovery_checks if item["severity"] == "error"]
        )
        checks.extend(_harness_checks(home, skills))
        index_result = update_skill_index(skills_root, index_path, write=False)
        if index_result["exit_code"]:
            checks.append(
                check(
                    "error",
                    "skill-index-drift",
                    f"Skill index is stale; run index --write: {index_path}",
                    path=str(index_path),
                )
            )
    worktrees: list[dict[str, Any]] = []
    docs_audit: dict[str, Any] = {}
    if args.full:
        if "skills" in sections:
            implicit_skills = sorted(
                name
                for name, allow_implicit in HARNESS_INVOCATION_POLICY.items()
                if allow_implicit
            )
            checks.extend(_runtime_visibility_checks(implicit_skills))
        if "worktrees" in sections:
            roots = args.repo_root or _default_repo_roots(home)
            worktrees, worktree_checks = scan_worktrees(roots)
            checks.extend(worktree_checks)
        if "docs" in sections:
            roots = args.repo_root or _default_repo_roots(home)
            docs_audit, docs_checks = scan_documents(
                roots,
                memory_root=home / ".codex" / "memories",
            )
            checks.extend(docs_checks)
    elif not _has_errors(checks):
        checks.append(check("ok", "harness-core-healthy", "Core Harness checks passed"))
    report = make_report(
        checks=checks,
        worktrees=worktrees,
        docs_audit=docs_audit,
        scope="full" if args.full else "core",
        sections=sections,
    )
    sys.stdout.write(render_report(report, args.format))
    return report_exit_code(report, strict=args.strict)

def _index_command(args: argparse.Namespace) -> int:
    skills_root = args.skills_root.expanduser()
    index_path = args.index_path.expanduser()
    result = update_skill_index(skills_root, index_path, write=args.write)
    for item in result["checks"]:
        print(f"[{item['severity'].upper()}] {item['code']}: {item['message']}")
    if result["exit_code"] == 0:
        action = "updated" if args.write and result["changed"] else "current"
        print(f"Skill index is {action}: {index_path}")
    elif not _has_errors(result["checks"]):
        print(f"Skill index is stale: {index_path}")
    return result["exit_code"]


def _cleanup_command(args: argparse.Namespace) -> int:
    home = Path.home()
    roots = args.repo_root or _default_repo_roots(home)
    records, checks = cleanup_worktrees(
        roots,
        older_than_days=args.older_than_days,
        dry_run=args.dry_run,
    )
    status_counts: dict[str, int] = {}
    for record in records:
        status = record["cleanup_status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    report = {
        "version": REPORT_VERSION,
        "scope": "cleanup",
        "safe": True,
        "dry_run": args.dry_run,
        "older_than_days": args.older_than_days,
        "summary": {
            "errors": sum(item["severity"] == "error" for item in checks),
            "warnings": sum(item["severity"] == "warning" for item in checks),
            "inspected": len(records),
            "statuses": status_counts,
        },
        "checks": checks,
        "worktrees": records,
    }
    if args.format == "json":
        sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    else:
        mode = "dry-run" if args.dry_run else "apply"
        print(
            f"Harness cleanup ({mode}) older_than_days={args.older_than_days} "
            f"inspected={len(records)} errors={report['summary']['errors']}"
        )
        for status, count in sorted(status_counts.items()):
            print(f"[{status}] {count}")
        for item in checks:
            print(f"[{item['severity'].upper()}] {item['code']}: {item['message']}")
    return 1 if report["summary"]["errors"] else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser("doctor", help="Run read-only Harness checks")
    doctor_parser.add_argument("--format", choices=("human", "json"), default="human")
    doctor_parser.add_argument("--strict", action="store_true")
    doctor_parser.add_argument(
        "--full",
        action="store_true",
        help="Include extended skill and worktree checks, or selected docs checks",
    )
    doctor_parser.add_argument(
        "--repo-root",
        action="append",
        type=Path,
        help="Repository search root; repeat to scan more than one root",
    )
    doctor_parser.add_argument(
        "--section",
        action="append",
        choices=("skills", "worktrees", "docs"),
        help="Limit a full report to one or more sections; repeat as needed",
    )
    doctor_parser.set_defaults(handler=_doctor_command)

    index_parser = subparsers.add_parser("index", help="Check or update the skill index")
    mode = index_parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    index_parser.add_argument(
        "--skills-root",
        type=Path,
        default=Path.home() / ".agents" / "skills",
    )
    index_parser.add_argument(
        "--index-path",
        type=Path,
        default=Path.home() / ".agents" / "skills-index.md",
    )
    index_parser.set_defaults(handler=_index_command)

    cleanup_parser = subparsers.add_parser(
        "cleanup",
        help="Remove only old, merged, clean, inactive Codex worktrees",
    )
    cleanup_parser.add_argument(
        "--safe",
        action="store_true",
        required=True,
        help="Acknowledge the command's fail-closed safety policy",
    )
    cleanup_parser.add_argument("--older-than-days", type=int, default=7)
    cleanup_parser.add_argument("--dry-run", action="store_true")
    cleanup_parser.add_argument("--format", choices=("human", "json"), default="human")
    cleanup_parser.add_argument(
        "--repo-root",
        action="append",
        type=Path,
        help="Repository search root; repeat to scan more than one root",
    )
    cleanup_parser.set_defaults(handler=_cleanup_command)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "older_than_days", 0) < 0:
        parser.error("--older-than-days must be zero or greater")
    if getattr(args, "section", None) and not getattr(args, "full", False):
        parser.error("--section requires --full")
    try:
        return args.handler(args)
    except (OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
