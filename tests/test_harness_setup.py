import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 and earlier.
    tomllib = None


ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "scripts" / "harness_setup.py"
RECOVERY_DOC = ROOT / "docs" / "RECOVERY.md"
ROOT_MANIFEST = json.loads((ROOT / "profiles.json").read_text(encoding="utf-8"))
class HarnessSetupCliTests(unittest.TestCase):
    def run_raw(self, *args: str, source_root: Path = ROOT) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SETUP), *args, "--source-root", str(source_root)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_setup(self, home: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        return subprocess.run(
            [sys.executable, str(SETUP), *args, "--home", str(home)],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def make_skill_link(self, home: Path, name: str, target: Optional[Path] = None) -> Path:
        skills = home.resolve() / ".agents" / "skills"
        skills.mkdir(parents=True, exist_ok=True)
        destination = skills / name
        destination.symlink_to(target or (ROOT / ".agents" / "skills" / name), target_is_directory=True)
        return destination

    def find_backup_entries(self, home: Path, relative: Path) -> list[Path]:
        backup_root = home / ".codex-harness-backups"
        if not backup_root.is_dir():
            return []
        return [
            candidate
            for stamp in backup_root.iterdir()
            for candidate in [stamp / relative]
            if candidate.exists() or candidate.is_symlink()
        ]

    def test_core_profile_contains_exactly_five_skills(self) -> None:
        core_skills = {
            name
            for name, metadata in ROOT_MANIFEST["skills"].items()
            if metadata["profile"] == "core"
        }

        self.assertEqual(
            {
                "harness-engineering",
                "codebase-design",
                "diagnosing-bugs",
                "domain-modeling",
                "tdd",
            },
            core_skills,
        )

    def test_public_manifest_has_no_private_overlay_catalog(self) -> None:
        self.assertNotIn("overlay", ROOT_MANIFEST)

    def test_global_links_contain_no_custom_agent_configs(self) -> None:
        self.assertEqual(
            [],
            [
                entry
                for entry in ROOT_MANIFEST["global_links"]
                if entry["destination"].startswith(".codex/agents/")
            ],
        )

    def test_public_tree_has_no_internal_project_identifiers(self) -> None:
        forbidden = (
            "dy" + "cx",
            "shan" + "shui",
            "codex-" + "dy" + "cx-skills",
            "Documents/jobs/" + "dy" + "cx",
            "/Users/" + "anonym",
        )
        findings = []
        for path in ROOT.rglob("*"):
            relative = path.relative_to(ROOT)
            if ".git" in relative.parts or "__pycache__" in relative.parts or not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8").lower()
            except UnicodeDecodeError:
                continue
            for marker in forbidden:
                if marker.lower() in content:
                    findings.append(f"{relative}: {marker}")

        self.assertEqual([], findings)

    def test_install_leaves_machine_specific_codex_config_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config = home / ".codex" / "config.toml"
            config.parent.mkdir(parents=True)
            original = "[agents]\nenabled = true\nmax_concurrent_threads_per_session = 5\n"
            config.write_text(original, encoding="utf-8")

            result = self.run_setup(home, "install", "--profile", "core")

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertTrue(config.is_file())
            self.assertFalse(config.is_symlink())
            self.assertEqual(original, config.read_text(encoding="utf-8"))
            self.assertEqual(
                [],
                self.find_backup_entries(home, Path(".codex/config.toml")),
            )

    def test_install_does_not_create_machine_specific_codex_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)

            result = self.run_setup(home, "install", "--profile", "core")

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertFalse((home / ".codex" / "config.toml").exists())

    def test_install_retires_removed_distribution_link_to_backup_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            retired = self.make_skill_link(home, "ask-matt")

            first = self.run_setup(home, "install", "--profile", "core")

            self.assertEqual(first.returncode, 0, first.stderr or first.stdout)
            self.assertFalse(retired.is_symlink())
            backups = self.find_backup_entries(home, Path(".agents/skills/ask-matt"))
            self.assertEqual(1, len(backups))
            self.assertTrue(backups[0].is_symlink())
            self.assertEqual(
                ROOT / ".agents" / "skills" / "ask-matt",
                backups[0].readlink(),
            )
            self.assertIn("retired=1", first.stdout)

            second = self.run_setup(home, "install", "--profile", "core")
            self.assertEqual(second.returncode, 0, second.stderr or second.stdout)
            self.assertIn("retired=0", second.stdout)
            self.assertEqual(
                1,
                len(self.find_backup_entries(home, Path(".agents/skills/ask-matt"))),
            )

    def test_retired_link_dry_run_only_reports_without_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            retired = self.make_skill_link(home, "grill-with-docs")

            result = self.run_setup(
                home,
                "install",
                "--profile",
                "core",
                "--dry-run",
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertTrue(retired.is_symlink())
            self.assertFalse((home / ".codex-harness-backups").exists())
            self.assertIn(f"dry-run retire: {retired}", result.stdout)
            self.assertIn("retired=1", result.stdout)

    def test_check_reports_retired_distribution_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            retired = self.make_skill_link(home, "handoff")

            result = self.run_setup(home, "check", "--profile", "core")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(f"link: retired {retired}", result.stderr)

    def test_install_preserves_user_owned_retired_name_and_external_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            user_owned = home / ".agents" / "skills" / "ask-matt"
            user_owned.mkdir(parents=True)
            (user_owned / "notes.txt").write_text("mine\n", encoding="utf-8")
            external_root = home / "external-skills"
            external_target = external_root / "handoff"
            external_target.mkdir(parents=True)
            external = self.make_skill_link(home, "handoff", external_target)

            result = self.run_setup(home, "install", "--profile", "core")

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual("mine\n", (user_owned / "notes.txt").read_text(encoding="utf-8"))
            self.assertTrue(external.is_symlink())
            self.assertEqual(external_target.resolve(), external.resolve())
            self.assertIn("retired=0", result.stdout)

    def test_core_install_does_not_retire_daily_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            daily = self.make_skill_link(home, "web-access")

            result = self.run_setup(home, "install", "--profile", "core")

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertTrue(daily.is_symlink())
            self.assertEqual(
                (ROOT / ".agents" / "skills" / "web-access").resolve(),
                daily.resolve(),
            )
            self.assertIn("retired=0", result.stdout)

    def test_daily_install_includes_core_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)

            first = self.run_setup(home, "install", "--profile", "daily")
            self.assertEqual(first.returncode, 0, first.stderr or first.stdout)
            self.assertTrue((home / ".codex" / "AGENTS.md").is_symlink())
            self.assertTrue((home / ".agents" / "skills" / "harness-engineering").is_symlink())
            self.assertTrue((home / ".agents" / "skills" / "web-access").is_symlink())
            self.assertIn("validation: index=skipped(custom-home)", first.stdout)
            self.assertIn("validation: doctor=skipped(custom-home)", first.stdout)

            second = self.run_setup(home, "install", "--profile", "daily")
            self.assertEqual(second.returncode, 0, second.stderr or second.stdout)
            self.assertIn("unchanged", second.stdout)

    def test_real_home_install_runs_index_and_doctor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / "home"
            source_root = base / "distribution"
            doctor = (
                source_root
                / ".agents"
                / "skills"
                / "harness-engineering"
                / "scripts"
                / "harness_doctor.py"
            )
            doctor.parent.mkdir(parents=True)
            doctor.write_text(
                "import os, sys\n"
                "with open(os.environ['HARNESS_DOCTOR_LOG'], 'a', encoding='utf-8') as handle:\n"
                "    handle.write('|'.join(sys.argv[1:]) + '\\n')\n",
                encoding="utf-8",
            )
            manifest = {
                "version": 1,
                "distribution": {"name": "fixture", "repository": "fixture/repo"},
                "global_links": [],
                "profiles": {"core": {"description": "Fixture.", "includes": []}},
                "dependency_checks": [],
                "skills": {
                    "harness-engineering": {
                        "profile": "core",
                        "description": "Fixture.",
                        "dependencies": [],
                        "credentials": "none",
                        "validation": "fixture",
                    }
                },
            }
            (source_root / "profiles.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            generated = self.run_raw("docs", "--write", source_root=source_root)
            self.assertEqual(generated.returncode, 0, generated.stderr or generated.stdout)

            log = base / "doctor.log"
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["HARNESS_DOCTOR_LOG"] = str(log)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SETUP),
                    "install",
                    "--profile",
                    "core",
                    "--source-root",
                    str(source_root),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(
                log.read_text(encoding="utf-8").splitlines(),
                ["index|--write", "index|--check", "doctor"],
            )
            self.assertIn("validation: index=ok", result.stdout)
            self.assertIn("validation: doctor=ok", result.stdout)

    def test_generic_overlay_uses_its_own_manifest_and_skill_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / "home"
            overlay = base / "private-overlay"
            skill_names = ["private-project-map", "private-release-check"]
            overlay_skills = {}
            for name in skill_names:
                skill = overlay / ".agents" / "skills" / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: Test fixture.\n---\n",
                    encoding="utf-8",
                )
                overlay_skills[name] = {
                    "profile": "private",
                    "description": "Test fixture.",
                    "dependencies": [],
                    "credentials": "none",
                    "validation": "fixture",
                }
            (overlay / "profiles.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "profiles": {"private": {"includes": []}},
                        "skills": overlay_skills,
                    }
                ),
                encoding="utf-8",
            )

            result = self.run_setup(
                home,
                "install",
                "--profile",
                "core",
                "--overlay-source",
                str(overlay),
                "--overlay-profile",
                "private",
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            installed = home / ".agents" / "skills" / "private-project-map"
            self.assertTrue(installed.is_symlink())
            self.assertEqual(
                installed.resolve(),
                (overlay / ".agents" / "skills" / "private-project-map").resolve(),
            )
            checked = self.run_setup(
                home,
                "check",
                "--profile",
                "core",
                "--overlay-source",
                str(overlay),
                "--overlay-profile",
                "private",
            )
            self.assertEqual(checked.returncode, 0, checked.stderr or checked.stdout)

    def test_overlay_source_and_profile_are_required_together_without_mutating_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cases = (
                ("--overlay-source", str(base / "overlay")),
                ("--overlay-profile", "private"),
            )
            for index, args in enumerate(cases):
                with self.subTest(args=args):
                    home = base / f"home-{index}"
                    result = self.run_setup(home, "install", "--profile", "core", *args)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(
                        "--overlay-source and --overlay-profile must be provided together",
                        result.stderr,
                    )
                    self.assertFalse((home / ".codex").exists())
                    self.assertFalse((home / ".agents").exists())
                    self.assertFalse((home / ".codex-harness-backups").exists())

    def test_overlay_rejects_missing_source_and_unknown_profile_without_mutating_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            overlay = base / "overlay"
            overlay.mkdir()
            (overlay / "profiles.json").write_text(
                json.dumps({"version": 1, "profiles": {"private": {"includes": []}}, "skills": {}}),
                encoding="utf-8",
            )
            cases = (
                (base / "missing", "private", "overlay source not found"),
                (overlay, "unknown", "unknown profile"),
            )
            for index, (source, profile, expected) in enumerate(cases):
                with self.subTest(source=source, profile=profile):
                    home = base / f"home-{index}"
                    result = self.run_setup(
                        home,
                        "install",
                        "--profile",
                        "core",
                        "--overlay-source",
                        str(source),
                        "--overlay-profile",
                        profile,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(expected, result.stderr)
                    self.assertFalse((home / ".codex").exists())
                    self.assertFalse((home / ".agents").exists())
                    self.assertFalse((home / ".codex-harness-backups").exists())

    def test_docs_check_matches_generated_skill_inventory(self) -> None:
        result = self.run_raw("docs", "--check")

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertIn("docs: ok", result.stdout)

    def test_security_check_rejects_local_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp)
            local_config = source_root / ".agents" / "skills" / "web-access" / "config.env"
            local_config.parent.mkdir(parents=True)
            local_config.write_text("WEB_ACCESS_BROWSER=chrome\n", encoding="utf-8")

            result = self.run_raw("security", "--check", source_root=source_root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("forbidden path", result.stderr)

    def test_security_check_allows_git_ignored_local_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp)
            local_config = source_root / ".agents" / "skills" / "web-access" / "config.env"
            local_config.parent.mkdir(parents=True)
            local_config.write_text("WEB_ACCESS_BROWSER=chrome\n", encoding="utf-8")
            (source_root / ".gitignore").write_text("config.env\n", encoding="utf-8")
            initialized = subprocess.run(
                ["git", "init", "-q"], cwd=source_root, check=False
            )
            self.assertEqual(initialized.returncode, 0)

            result = self.run_raw("security", "--check", source_root=source_root)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertIn("security: ok", result.stdout)

    def test_dry_run_does_not_create_home_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "new-home"

            result = self.run_setup(home, "install", "--profile", "daily", "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertFalse((home / ".codex").exists())
            self.assertFalse((home / ".agents").exists())
            self.assertFalse((home / ".codex-harness-backups").exists())
            self.assertIn("dry-run", result.stdout)

    def test_conflicting_file_is_backed_up_before_linking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            agents = home / ".codex" / "AGENTS.md"
            agents.parent.mkdir(parents=True)
            agents.write_text("user-owned\n", encoding="utf-8")

            result = self.run_setup(home, "install", "--profile", "core")

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertTrue(agents.is_symlink())
            backups = list((home / ".codex-harness-backups").glob("*/.codex/AGENTS.md"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "user-owned\n")

    def test_docs_check_rejects_inventory_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp)
            (source_root / "docs").mkdir()
            (source_root / "profiles.json").write_text(
                (ROOT / "profiles.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (source_root / "docs" / "SKILLS.md").write_text("stale\n", encoding="utf-8")

            result = self.run_raw("docs", "--check", source_root=source_root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("drift detected", result.stderr)

    def test_security_check_rejects_hardcoded_database_password(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp)
            script = source_root / "scripts" / "db.sh"
            script.parent.mkdir(parents=True)
            script.write_text('DB_PASSWORD="not-a-placeholder"\n', encoding="utf-8")

            result = self.run_raw("security", "--check", source_root=source_root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("hardcoded DB password", result.stderr)

    def test_check_fails_before_install_and_passes_after_core_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)

            missing = self.run_setup(home, "check", "--profile", "core")
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("link: missing", missing.stderr)

            installed = self.run_setup(home, "install", "--profile", "core")
            self.assertEqual(installed.returncode, 0, installed.stderr or installed.stdout)

            checked = self.run_setup(home, "check", "--profile", "core")
            self.assertEqual(checked.returncode, 0, checked.stderr or checked.stdout)
            self.assertIn("check: ok", checked.stdout)

    def test_credentials_set_uses_keychain_prompt_without_password_argument(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / "home"
            overlay = base / "overlay"
            overlay.mkdir()
            (overlay / "profiles.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "profiles": {"private": {"includes": []}},
                        "skills": {},
                        "credentials": {
                            "fixture-db": {
                                "service": "codex-fixture-db",
                                "account": "fixture-user",
                                "environment": "FIXTURE_DB_PASSWORD",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            log = base / "security.log"
            fake_security = base / "security"
            fake_security.write_text(
                "#!/bin/sh\n"
                "printf 'CALL' >> \"$HARNESS_SECURITY_LOG\"\n"
                "for arg in \"$@\"; do printf '|%s' \"$arg\" >> \"$HARNESS_SECURITY_LOG\"; done\n"
                "printf '\\n' >> \"$HARNESS_SECURITY_LOG\"\n",
                encoding="utf-8",
            )
            fake_security.chmod(0o755)
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["HARNESS_SECURITY_LOG"] = str(log)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SETUP),
                    "credentials",
                    "set",
                    "fixture-db",
                    "--overlay-source",
                    str(overlay),
                    "--security-bin",
                    str(fake_security),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            calls = log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                calls[0],
                "CALL|add-generic-password|-U|-a|fixture-user|-s|codex-fixture-db|-w",
            )


if __name__ == "__main__":
    unittest.main()
