#!/usr/bin/env python3
"""Install and validate the portable Codex Harness distribution."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


DEFAULT_SOURCE_ROOT = Path(__file__).resolve().parents[1]


class SetupError(RuntimeError):
    pass


@dataclass(frozen=True)
class LinkSpec:
    source: Path
    destination: Path


def load_manifest(source_root: Path) -> dict:
    manifest_path = source_root / "profiles.json"
    if not manifest_path.is_file():
        raise SetupError(f"manifest not found: {manifest_path}")
    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest.get("version") != 1:
        raise SetupError(f"unsupported manifest version: {manifest.get('version')!r}")
    return manifest


def resolve_home(args: argparse.Namespace) -> Path:
    return (args.home or Path.home()).expanduser().resolve()


def resolve_profiles(manifest: dict, requested: str) -> list[str]:
    profiles = manifest.get("profiles", {})
    if requested not in profiles:
        raise SetupError(f"unknown profile: {requested}")

    resolved: list[str] = []
    visiting: set[str] = set()

    def visit(name: str) -> None:
        if name in resolved:
            return
        if name in visiting:
            raise SetupError(f"profile include cycle: {name}")
        if name not in profiles:
            raise SetupError(f"unknown included profile: {name}")
        visiting.add(name)
        for included in profiles[name].get("includes", []):
            visit(included)
        visiting.remove(name)
        resolved.append(name)

    visit(requested)
    return resolved


def ensure_source_inside_root(source: Path, root: Path) -> Path:
    resolved_source = source.resolve(strict=True)
    resolved_root = root.resolve(strict=True)
    try:
        resolved_source.relative_to(resolved_root)
    except ValueError as exc:
        raise SetupError(f"source escapes repository root: {source}") from exc
    return resolved_source


def build_skill_links(source_root: Path, home: Path, manifest: dict, profile: str) -> list[LinkSpec]:
    selected_profiles = set(resolve_profiles(manifest, profile))
    links: list[LinkSpec] = []

    for name, metadata in manifest.get("skills", {}).items():
        if metadata.get("profile") not in selected_profiles:
            continue
        source = ensure_source_inside_root(source_root / ".agents" / "skills" / name, source_root)
        links.append(LinkSpec(source, home / ".agents" / "skills" / name))

    return links


def build_main_links(source_root: Path, home: Path, manifest: dict, profile: str) -> list[LinkSpec]:
    links = [
        LinkSpec(
            ensure_source_inside_root(source_root / entry["source"], source_root),
            home / entry["destination"],
        )
        for entry in manifest.get("global_links", [])
    ]
    links.extend(build_skill_links(source_root, home, manifest, profile))
    return links


def load_overlay(args: argparse.Namespace) -> Optional[tuple[Path, dict, set[str]]]:
    if bool(args.overlay_source) != bool(args.overlay_profile):
        raise SetupError("--overlay-source and --overlay-profile must be provided together")
    if args.overlay_source is None:
        return None

    source = args.overlay_source.expanduser().resolve()
    if not source.is_dir():
        raise SetupError(f"overlay source not found: {source}")
    manifest = load_manifest(source)
    profiles = set(resolve_profiles(manifest, args.overlay_profile))
    return source, manifest, profiles


def link_matches(destination: Path, source: Path) -> bool:
    if not destination.is_symlink():
        return False
    try:
        return destination.resolve(strict=True) == source
    except FileNotFoundError:
        return False


def install_links(links: Iterable[LinkSpec], home: Path, dry_run: bool) -> tuple[int, int, list[Path]]:
    changed = 0
    unchanged = 0
    backups: list[Path] = []
    backup_root: Optional[Path] = None

    for link in links:
        if link_matches(link.destination, link.source):
            unchanged += 1
            print(f"unchanged: {link.destination}")
            continue

        exists = link.destination.exists() or link.destination.is_symlink()
        if dry_run:
            action = "replace" if exists else "link"
            print(f"dry-run {action}: {link.destination} -> {link.source}")
            changed += 1
            continue

        link.destination.parent.mkdir(parents=True, exist_ok=True)
        if exists:
            if backup_root is None:
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
                backup_root = home / ".codex-harness-backups" / stamp
            relative = link.destination.relative_to(home)
            backup = backup_root / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(link.destination), str(backup))
            backups.append(backup)
            print(f"backup: {link.destination} -> {backup}")

        link.destination.symlink_to(link.source, target_is_directory=link.source.is_dir())
        changed += 1
        print(f"linked: {link.destination} -> {link.source}")

    return changed, unchanged, backups


def find_retired_skill_links(source_root: Path, home: Path, manifest: dict) -> list[Path]:
    skills_root = home / ".agents" / "skills"
    if skills_root.is_symlink() or not skills_root.is_dir():
        return []

    active_names = set(manifest.get("skills", {}))
    distribution_skills = source_root / ".agents" / "skills"
    retired: list[Path] = []
    for destination in sorted(skills_root.iterdir()):
        if not destination.is_symlink() or destination.name in active_names:
            continue
        target = Path(os.readlink(destination))
        if not target.is_absolute():
            target = destination.parent / target
        expected = distribution_skills / destination.name
        if target.resolve(strict=False) == expected.resolve(strict=False):
            retired.append(destination)
    return retired


def retire_skill_links(
    links: Iterable[Path], home: Path, dry_run: bool
) -> tuple[int, list[Path]]:
    retired = 0
    backups: list[Path] = []
    backup_root: Optional[Path] = None
    for destination in links:
        if dry_run:
            print(f"dry-run retire: {destination}")
            retired += 1
            continue

        if backup_root is None:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
            backup_root = home / ".codex-harness-backups" / stamp
        relative = destination.relative_to(home)
        backup = backup_root / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(destination), str(backup))
        backups.append(backup)
        retired += 1
        print(f"retired: {destination} -> {backup}")
    return retired, backups


def command_install(args: argparse.Namespace) -> int:
    source_root = args.source_root.expanduser().resolve()
    home = resolve_home(args)
    manifest = load_manifest(source_root)
    links = build_main_links(source_root, home, manifest, args.profile)
    selected_profiles = set(resolve_profiles(manifest, args.profile))
    roots_to_scan = [source_root]
    manifests_for_dependencies = [manifest]
    overlay = load_overlay(args)

    if overlay is not None:
        overlay_source, overlay_manifest, overlay_profiles = overlay
        links.extend(
            build_skill_links(overlay_source, home, overlay_manifest, args.overlay_profile)
        )
        selected_profiles.update(overlay_profiles)
        roots_to_scan.append(overlay_source)
        manifests_for_dependencies.append(overlay_manifest)

    validate_install_sources(source_root, manifest, roots_to_scan)
    retired, retired_backups = retire_skill_links(
        find_retired_skill_links(source_root, home, manifest),
        home,
        args.dry_run,
    )
    changed, unchanged, backups = install_links(links, home, args.dry_run)
    print(
        f"summary: changed={changed} unchanged={unchanged} retired={retired} "
        f"backups={len(backups) + len(retired_backups)}"
    )

    action_required = sum(
        check_dependencies(candidate, selected_profiles) for candidate in manifests_for_dependencies
    )
    dependency_result = "ready" if action_required == 0 else f"action-required={action_required}"
    print(f"validation: dependencies={dependency_result}")

    if args.dry_run:
        print("validation: index=skipped(dry-run)")
        print("validation: doctor=skipped(dry-run)")
    elif args.home is not None:
        print("validation: index=skipped(custom-home)")
        print("validation: doctor=skipped(custom-home)")
    else:
        run_harness_health(home)
    return 0


def markdown_cell(value: object) -> str:
    if isinstance(value, list):
        text = ", ".join(str(item) for item in value) or "none"
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def render_skill_inventory(manifest: dict) -> str:
    lines = [
        "# Skill Inventory",
        "",
        "Generated from `profiles.json` by `scripts/harness_setup.py docs --write`. Do not edit",
        "this file by hand.",
        "",
        "## Profiles",
        "",
    ]
    for name, metadata in manifest.get("profiles", {}).items():
        includes = metadata.get("includes", [])
        suffix = f" Includes: {', '.join(includes)}." if includes else ""
        lines.append(f"- `{name}`: {metadata['description']}{suffix}")

    lines.extend(
        [
            "## Skills",
            "",
            "| Profile | Skill | Source | Purpose | Dependencies | Credentials | Validation |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    profile_order = {name: index for index, name in enumerate(manifest.get("profiles", {}))}
    entries = []
    for name, metadata in manifest.get("skills", {}).items():
        entries.append(
            {
                "name": name,
                "profile": metadata["profile"],
                "source": manifest["distribution"]["name"],
                **metadata,
            }
        )

    entries.sort(key=lambda item: (profile_order.get(item["profile"], 99), item["name"]))
    for entry in entries:
        cells = [
            f"`{entry['profile']}`",
            f"`{entry['name']}`",
            f"`{entry['source']}`",
            markdown_cell(entry["description"]),
            markdown_cell(entry["dependencies"]),
            markdown_cell(entry["credentials"]),
            markdown_cell(entry["validation"]),
        ]
        lines.append("| " + " | ".join(cells) + " |")

    lines.extend(
        [
            "",
            "## Exclusions",
            "",
            "Codex-managed system skills, credentials, sessions, memory, caches, machine-specific",
            "`~/.codex/config.toml`, real env files, and private keys are not distributed.",
            "",
        ]
    )
    return "\n".join(lines)


def command_docs(args: argparse.Namespace) -> int:
    source_root = args.source_root.expanduser().resolve()
    manifest = load_manifest(source_root)
    rendered = render_skill_inventory(manifest)
    destination = source_root / "docs" / "SKILLS.md"

    if args.write:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8")
        print(f"docs: wrote {destination}")
        return 0

    if not destination.is_file() or destination.read_text(encoding="utf-8") != rendered:
        raise SetupError(f"docs: drift detected in {destination}; run docs --write")
    print("docs: ok")
    return 0


def is_placeholder_secret(value: str) -> bool:
    normalized = value.strip().strip('"\'`').strip()
    lowered = normalized.lower()
    return (
        not normalized
        or normalized.startswith("$")
        or normalized.startswith("<")
        or lowered in {"none", "redacted", "password", "pass", "prompt", "example"}
    )


def is_git_ignored(source_root: Path, path: Path) -> bool:
    if shutil.which("git") is None:
        return False
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(source_root),
            "check-ignore",
            "--quiet",
            "--",
            str(path.relative_to(source_root)),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def security_findings(source_root: Path) -> list[str]:
    findings: list[str] = []
    private_key = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
    github_token = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")
    db_assignment = re.compile(r"(?im)^\s*(?:export\s+)?DB_PASSWORD\s*=\s*([^\s#]+)")
    db_documentation = re.compile(r"(?im)^\s*-\s*DB password:\s*(.+)$")

    for path in sorted(source_root.rglob("*")):
        relative = path.relative_to(source_root)
        if not relative.parts:
            continue
        if relative.parts[0] == ".git":
            continue

        if ".git" in relative.parts:
            findings.append(f"forbidden path: {relative}")
            continue
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            findings.append(f"forbidden path: {relative}")
            continue
        if path.name == "config.env":
            if is_git_ignored(source_root, path):
                continue
            findings.append(f"forbidden path: {relative}")
            continue
        if relative.as_posix() == ".codex/config.toml":
            findings.append(f"forbidden path: {relative}")
            continue
        if path.suffix.lower() in {".key", ".pem", ".p12", ".pfx"}:
            findings.append(f"forbidden path: {relative}")
            continue
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if private_key.search(content):
            findings.append(f"private key content: {relative}")
        if github_token.search(content):
            findings.append(f"GitHub token content: {relative}")
        for match in db_assignment.finditer(content):
            if not is_placeholder_secret(match.group(1)):
                findings.append(f"hardcoded DB password: {relative}")
                break
        for match in db_documentation.finditer(content):
            if not is_placeholder_secret(match.group(1)):
                findings.append(f"documented DB password: {relative}")
                break

    return findings


def command_security(args: argparse.Namespace) -> int:
    source_root = args.source_root.expanduser().resolve()
    findings = security_findings(source_root)
    if findings:
        for finding in findings:
            print(f"error: {finding}", file=sys.stderr)
        return 1
    print("security: ok")
    return 0


def validate_install_sources(source_root: Path, manifest: dict, roots: Iterable[Path]) -> None:
    expected_docs = render_skill_inventory(manifest)
    skills_doc = source_root / "docs" / "SKILLS.md"
    if not skills_doc.is_file() or skills_doc.read_text(encoding="utf-8") != expected_docs:
        raise SetupError(f"docs: drift detected in {skills_doc}; run docs --write")
    print("validation: docs=ok")

    findings = []
    for root in roots:
        findings.extend(security_findings(root))
    if findings:
        raise SetupError("security check failed: " + "; ".join(findings))
    print("validation: security=ok")


def run_harness_health(home: Path) -> None:
    doctor = home / ".agents" / "skills" / "harness-engineering" / "scripts" / "harness_doctor.py"
    if not doctor.is_file():
        raise SetupError(f"Harness Doctor not found after installation: {doctor}")

    for command in (("index", "--write"), ("index", "--check")):
        completed = subprocess.run([sys.executable, str(doctor), *command], check=False)
        if completed.returncode != 0:
            raise SetupError(f"Harness index failed: {' '.join(command)}")
    print("validation: index=ok")

    completed = subprocess.run([sys.executable, str(doctor), "doctor"], check=False)
    if completed.returncode != 0:
        raise SetupError("Harness Doctor failed")
    print("validation: doctor=ok")


def check_links(links: Iterable[LinkSpec]) -> list[str]:
    findings: list[str] = []
    for link in links:
        if not (link.destination.exists() or link.destination.is_symlink()):
            findings.append(f"link: missing {link.destination}")
        elif not link_matches(link.destination, link.source):
            findings.append(f"link: drift {link.destination} expected {link.source}")
    return findings


def dependency_state(entry: dict, manifest: dict) -> bool:
    kind = entry["kind"]
    if kind == "command":
        return shutil.which(entry["value"]) is not None
    if kind == "gh-auth":
        if shutil.which(entry["value"]) is None:
            return False
        completed = subprocess.run(
            [entry["value"], "auth", "status"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return completed.returncode == 0
    if kind == "path-any":
        return any(Path(value).expanduser().exists() for value in entry.get("values", []))
    if kind == "keychain-or-env":
        credential = manifest.get("credentials", {}).get(entry["credential"])
        if not credential:
            raise SetupError(f"unknown credential check: {entry['credential']}")
        if os.environ.get(credential["environment"]):
            return True
        security_bin = Path("/usr/bin/security")
        if not security_bin.is_file():
            return False
        completed = subprocess.run(
            [
                str(security_bin),
                "find-generic-password",
                "-s",
                credential["service"],
                "-a",
                credential["account"],
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return completed.returncode == 0
    raise SetupError(f"unsupported dependency check kind: {kind}")


def check_dependencies(manifest: dict, selected_profiles: set[str]) -> int:
    action_required = 0
    for entry in manifest.get("dependency_checks", []):
        if entry.get("profile") not in selected_profiles:
            continue
        if dependency_state(entry, manifest):
            state = "ready"
        else:
            state = entry.get("missing", "action-required")
            if state == "action-required":
                action_required += 1
        print(f"dependency: {state} {entry['id']}")
    return action_required


def command_check(args: argparse.Namespace) -> int:
    source_root = args.source_root.expanduser().resolve()
    home = resolve_home(args)
    manifest = load_manifest(source_root)
    selected_profiles = set(resolve_profiles(manifest, args.profile))
    links = build_main_links(source_root, home, manifest, args.profile)
    roots_to_scan = [source_root]
    manifests_for_dependencies = [manifest]

    overlay = load_overlay(args)
    if overlay is not None:
        overlay_source, overlay_manifest, overlay_profiles = overlay
        links.extend(
            build_skill_links(overlay_source, home, overlay_manifest, args.overlay_profile)
        )
        selected_profiles.update(overlay_profiles)
        roots_to_scan.append(overlay_source)
        manifests_for_dependencies.append(overlay_manifest)

    findings = check_links(links)
    findings.extend(
        f"link: retired {path}"
        for path in find_retired_skill_links(source_root, home, manifest)
    )
    expected_docs = render_skill_inventory(manifest)
    skills_doc = source_root / "docs" / "SKILLS.md"
    if not skills_doc.is_file() or skills_doc.read_text(encoding="utf-8") != expected_docs:
        findings.append(f"docs: drift detected in {skills_doc}")
    for root in roots_to_scan:
        findings.extend(security_findings(root))

    for finding in findings:
        print(f"error: {finding}", file=sys.stderr)

    action_required = sum(
        check_dependencies(candidate, selected_profiles) for candidate in manifests_for_dependencies
    )
    if findings or action_required:
        return 1
    print("check: ok")
    return 0


def command_credentials_set(args: argparse.Namespace) -> int:
    overlay_source = args.overlay_source.expanduser().resolve()
    if not overlay_source.is_dir():
        raise SetupError(f"overlay source not found: {overlay_source}")
    overlay_manifest = load_manifest(overlay_source)
    credential = overlay_manifest.get("credentials", {}).get(args.credential)
    if not credential:
        raise SetupError(f"unknown credential: {args.credential}")

    security_bin = args.security_bin.expanduser().resolve()
    if not security_bin.is_file():
        raise SetupError(f"macOS security tool not found: {security_bin}")
    add_command = [
        str(security_bin),
        "add-generic-password",
        "-U",
        "-a",
        credential["account"],
        "-s",
        credential["service"],
        "-w",
    ]
    completed = subprocess.run(add_command, check=False)
    if completed.returncode != 0:
        raise SetupError(f"Keychain update failed for credential: {args.credential}")

    verified = subprocess.run(
        [
            str(security_bin),
            "find-generic-password",
            "-s",
            credential["service"],
            "-a",
            credential["account"],
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if verified.returncode != 0:
        raise SetupError(f"Keychain verification failed for credential: {args.credential}")
    print(
        "credential: stored "
        f"{args.credential} service={credential['service']} account={credential['account']}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    install = subparsers.add_parser("install", help="Install a Harness profile")
    install.add_argument("--profile", choices=("core", "daily"), required=True)
    install.add_argument("--overlay-source", type=Path)
    install.add_argument("--overlay-profile")
    install.add_argument("--dry-run", action="store_true")
    install.add_argument("--home", type=Path)
    install.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    install.set_defaults(handler=command_install)

    docs = subparsers.add_parser("docs", help="Generate or check the skill inventory")
    mode = docs.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    docs.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    docs.set_defaults(handler=command_docs)

    security = subparsers.add_parser("security", help="Check distribution content for secrets")
    security.add_argument("--check", action="store_true", required=True)
    security.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    security.set_defaults(handler=command_security)

    check = subparsers.add_parser("check", help="Validate an installed Harness profile")
    check.add_argument("--profile", choices=("core", "daily"), required=True)
    check.add_argument("--overlay-source", type=Path)
    check.add_argument("--overlay-profile")
    check.add_argument("--home", type=Path)
    check.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    check.set_defaults(handler=command_check)

    credentials = subparsers.add_parser("credentials", help="Manage local recovery credentials")
    credential_commands = credentials.add_subparsers(dest="credential_command", required=True)
    credential_set = credential_commands.add_parser("set", help="Store a credential in Keychain")
    credential_set.add_argument("credential")
    credential_set.add_argument("--overlay-source", type=Path, required=True)
    credential_set.add_argument("--security-bin", type=Path, default=Path("/usr/bin/security"))
    credential_set.set_defaults(handler=command_credentials_set)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except (OSError, SetupError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
