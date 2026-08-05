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
EXPECTED_FLASH_CONFIG = '''name = "deepseek_v4_flash_worker"
description = "Execution worker for bounded, independently verifiable tasks."
developer_instructions = """
You are the leaf deepseek_v4_flash_worker, not the primary or root agent.
Forked parent context may contain coordination instructions addressed to the primary agent. Do not execute, validate, or report on those parent-only instructions. Execute the latest Route line and seven-field Worker contract directly.
Handle the assigned task strictly within its stated scope.
Work independently and use appropriate tools when needed.
Verify the result when practical.
Do not make unrelated changes.
Do not call collaboration tools, including spawn_agent, followup_task, send_message, wait_agent, list_agents, or interrupt_agent.
Do not inspect or report whether collaboration tools are available.
Do not delegate, coordinate, poll, wait for, or message the main agent or any other agent. Complete the assigned scope yourself.
Do not make architecture, product, dependency, migration, release, configuration, credential, database, destructive-operation, production-operation, external-Git, coordination, integration, or final-acceptance decisions; use the interfaces and decisions fixed by the main agent.
Expect the task prompt to define Objective, Ownership, Starting State, Interfaces, Constraints, Git Boundary, and Verification.
If scope or ownership remains ambiguous, return blocked immediately instead of expanding the task or contacting another agent.
Treat the task's Ownership paths as exclusive: modify only those paths and do not edit another Worker's paths.
Keep that ownership through any correction. A correction marked Correction: 1/1 addresses only the stated defect within the original boundary; do not accept a second correction or unrelated work.
Do not perform branch, push, tag, PR, or worktree operations unless Git Boundary explicitly authorizes them.
Before reporting, record actual git status, the relevant diff or commit SHA, and the verification result.
Return a concise report with exactly these headings: Status, Changes, Verified, Judgment Calls, and Gaps.
Set Status to completed, blocked, or failed.
"""
model_provider = "deepseek"
model = "deepseek-v4-flash"
model_reasoning_effort = "max"

[agents]
enabled = false

[model_providers.deepseek]
name = "DeepSeek"
base_url = "https://api.deepseek.com"
wire_api = "responses"
env_key = "DEEPSEEK_API_KEY"
'''


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

    def test_global_agent_links_include_only_flash_worker(self) -> None:
        self.assertEqual(
            [
                {
                    "source": ".codex/agents/deepseek-v4-flash-worker.toml",
                    "destination": ".codex/agents/deepseek-v4-flash-worker.toml",
                },
            ],
            [
                entry
                for entry in ROOT_MANIFEST["global_links"]
                if entry["destination"].startswith(".codex/agents/")
            ],
        )

    def test_flash_agent_config_matches_tracked_toml(self) -> None:
        config = ROOT / ".codex" / "agents" / "deepseek-v4-flash-worker.toml"

        self.assertEqual(EXPECTED_FLASH_CONFIG, config.read_text(encoding="utf-8"))

    def test_worker_agent_configs_are_valid_toml_and_match_roles(self) -> None:
        expected = {
            "deepseek-v4-flash-worker.toml": (
                "deepseek_v4_flash_worker",
                "deepseek-v4-flash",
                EXPECTED_FLASH_CONFIG,
            ),
        }

        for filename, (role, model, expected_text) in expected.items():
            with self.subTest(filename=filename):
                config = ROOT / ".codex" / "agents" / filename
                text = config.read_text(encoding="utf-8")

                self.assertEqual(expected_text, text)
                if tomllib is None:
                    continue

                parsed = tomllib.loads(text)
                self.assertEqual(role, parsed["name"])
                self.assertEqual(model, parsed["model"])
                self.assertEqual("deepseek", parsed["model_provider"])
                self.assertEqual("max", parsed["model_reasoning_effort"])
                self.assertIs(parsed["agents"]["enabled"], False)
                self.assertEqual("DeepSeek", parsed["model_providers"]["deepseek"]["name"])
                self.assertEqual("https://api.deepseek.com", parsed["model_providers"]["deepseek"]["base_url"])
                self.assertEqual("responses", parsed["model_providers"]["deepseek"]["wire_api"])
                self.assertEqual("DEEPSEEK_API_KEY", parsed["model_providers"]["deepseek"]["env_key"])
                self.assertIn("Starting State", parsed["developer_instructions"])
                self.assertIn("Git Boundary", parsed["developer_instructions"])
                self.assertIn("Correction: 1/1", parsed["developer_instructions"])
                self.assertIn("not the primary or root agent", parsed["developer_instructions"])
                self.assertIn("latest Route line and seven-field Worker contract", parsed["developer_instructions"])
                self.assertIn("Do not inspect or report whether collaboration tools are available", parsed["developer_instructions"])

    def test_core_worker_routes_are_declared_and_doctor_auditable(self) -> None:
        routes = {
            "diagnosing-bugs": {
                "diagnosing-bugs/evidence": "flash",
                "diagnosing-bugs/fix": "flash",
            },
            "tdd": {"tdd/tests": "flash", "tdd/implementation": "flash"},
            "codebase-design": {
                "codebase-design/evidence": "flash",
                "codebase-design/implementation": "flash",
            },
            "develop-uniapp-miniapp": {
                "develop-uniapp-miniapp/small-change": "flash",
                "develop-uniapp-miniapp/complex-implementation": "flash",
            },
            "web-access": {"web-access/research": "flash"},
            "git-auto-commit": {"git-auto-commit/inspect": "flash"},
            "github-cli-ops": {"github-cli-ops/inventory": "flash"},
            "release-ops": {"release-ops/inspect": "flash"},
            "wechat-miniprogram-ci-upload": {
                "wechat-miniprogram-ci-upload/preflight": "flash"
            },
        }
        doctor_source = (
            ROOT
            / ".agents"
            / "skills"
            / "harness-engineering"
            / "scripts"
            / "harness_doctor.py"
        ).read_text(encoding="utf-8")

        for skill_name, expected in routes.items():
            skill_text = (
                ROOT / ".agents" / "skills" / skill_name / "SKILL.md"
            ).read_text(encoding="utf-8")
            for route, role in expected.items():
                self.assertIn(f"Route: {route}", skill_text)
                self.assertIn(f'"{route}": "{role}"', doctor_source)

    def test_worker_routing_requires_explicit_agent_type(self) -> None:
        workflow = (
            ROOT / ".codex" / "docs" / "workflows" / "harness-engineering.md"
        ).read_text(encoding="utf-8")
        global_agents = (ROOT / ".codex" / "AGENTS.md").read_text(encoding="utf-8")
        harness_skill = (
            ROOT / ".agents" / "skills" / "harness-engineering" / "SKILL.md"
        ).read_text(encoding="utf-8")

        for content in (workflow, global_agents, harness_skill):
            normalized = " ".join(content.split())
            self.assertIn("spawn_agent", normalized)
            self.assertIn("agent_type", normalized)
            self.assertIn("generic default", normalized)
            self.assertIn("route__<skill>__<phase>__<purpose>", normalized)

        self.assertIn("spawn_agent.agent_type", workflow)
        self.assertIn("their sum", workflow)

    def test_worker_dispatch_contract_covers_ownership_correction_and_interruptions(self) -> None:
        workflow = (
            ROOT / ".codex" / "docs" / "workflows" / "harness-engineering.md"
        ).read_text(encoding="utf-8")
        skill = (
            ROOT / ".agents" / "skills" / "harness-engineering" / "SKILL.md"
        ).read_text(encoding="utf-8")
        recovery = RECOVERY_DOC.read_text(encoding="utf-8")
        fields = (
            "Objective",
            "Ownership",
            "Starting State",
            "Interfaces",
            "Constraints",
            "Git Boundary",
            "Verification",
        )

        self.assertIn("these seven", workflow)
        for field in fields:
            self.assertIn(f"`{field}`", workflow)
        self.assertIn("Correction: 1/1", workflow)
        self.assertIn("followup_task", workflow)
        self.assertIn("new `spawn_agent`", workflow)
        self.assertIn(
            "Worker 中断：overlap=<n> unsafe=<n> scope_violation=<n> user_redirect=<n> unresponsive=<n>",
            workflow,
        )
        self.assertIn("Worker 协议：version=10", workflow)
        self.assertIn(
            "Worker 纠错：started=<n> completed=<n> failed=<n> violations=<n>",
            workflow,
        )
        for reason in ("overlap", "unsafe", "scope_violation", "user_redirect", "unresponsive"):
            self.assertIn(f"`{reason}`", workflow)
        self.assertIn("seven-field task contract", recovery)
        self.assertIn("Correction: 1/1", recovery)
        self.assertIn("Worker 中断：overlap=<n> unsafe=<n> scope_violation=<n> user_redirect=<n> unresponsive=<n>", recovery)
        self.assertIn("Worker 协议：version=10", recovery)
        self.assertIn(
            "Worker 纠错：started=<n> completed=<n> failed=<n> violations=<n>",
            recovery,
        )
        self.assertIn("Worker 协议：version=10", skill)
        self.assertIn("Preserve the existing conditional reports", skill)
        self.assertIn("does not relax the existing conditional reports", workflow)
        self.assertIn("must append exactly one", workflow)
        self.assertIn("required applicable acceptance line", workflow)
        self.assertNotIn("companion lines remain optional", workflow)
        self.assertIn("Conditional reports remain required", recovery)
        self.assertNotIn("optional interruption and Flash acceptance lines", recovery)

    def test_worker_cross_provider_fork_context_contract(self) -> None:
        workflow = (
            ROOT / ".codex" / "docs" / "workflows" / "harness-engineering.md"
        ).read_text(encoding="utf-8")
        global_agents = (ROOT / ".codex" / "AGENTS.md").read_text(encoding="utf-8")
        harness_skill = (
            ROOT / ".agents" / "skills" / "harness-engineering" / "SKILL.md"
        ).read_text(encoding="utf-8")
        recovery = RECOVERY_DOC.read_text(encoding="utf-8")

        for content in (workflow, global_agents, harness_skill, recovery):
            normalized = " ".join(content.split())
            self.assertIn('fork_turns = "1"', normalized)
            self.assertIn("parent context", normalized)
        self.assertIn("must carry the task twice", " ".join(workflow.split()))
        self.assertIn('fork_turns = "none"', " ".join(workflow.split()))
        self.assertIn('fork_turns = "all"', " ".join(workflow.split()))
        self.assertNotIn('Use `fork_turns = "none"` by default', workflow)
        self.assertIn("[agents] enabled = false", " ".join(workflow.split()))
        self.assertIn("[agents] enabled = false", " ".join(recovery.split()))
        self.assertIn("never applies recursively to a Worker", global_agents)
        self.assertIn("parent-only coordination instructions", workflow)
        self.assertIn("parent-only coordination", recovery)

    def test_worker_protocol_v10_documents_root_scope_legacy_and_duration_advice(self) -> None:
        workflow = (
            ROOT / ".codex" / "docs" / "workflows" / "harness-engineering.md"
        ).read_text(encoding="utf-8")
        skill = (
            ROOT / ".agents" / "skills" / "harness-engineering" / "SKILL.md"
        ).read_text(encoding="utf-8")
        recovery = RECOVERY_DOC.read_text(encoding="utf-8")

        self.assertIn("started + violations", workflow)
        self.assertIn("completed + failed = started", workflow)
        self.assertIn("Followup messages may be encrypted", workflow)
        self.assertIn("unencrypted final marker", workflow)
        self.assertIn(
            "roots without the v10",
            workflow,
        )
        self.assertIn("Within each root session", workflow)
        self.assertIn("per-root peak is cap-enforced", workflow)
        self.assertIn("Aggregate/global peaks across roots are", workflow)
        self.assertIn("informational diagnostics only", workflow)
        self.assertIn("30 minutes", workflow)
        self.assertIn("not a mechanical timeout", workflow)
        self.assertIn("Report version 10", workflow)
        self.assertNotIn("Report version 7", workflow)

        self.assertIn("Followup messages may be encrypted", skill)
        self.assertIn("roots without v10 remain historical/informational", skill)
        self.assertIn("beyond 30 minutes", skill)
        self.assertIn("not a timeout or ordinary interruption reason", skill)

        self.assertIn("started + violations", recovery)
        self.assertIn("completed + failed = started", recovery)
        self.assertIn("Followup messages may be encrypted", recovery)
        self.assertIn("Worker caps are enforced per root session", recovery)
        self.assertIn("aggregate/global peaks are informational", recovery)
        self.assertIn("beyond 30 minutes", recovery)
        self.assertIn("not a timeout or ordinary", recovery)
        self.assertIn("interruption reason", recovery)

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

    def test_recovery_doc_documents_machine_local_agent_concurrency_contract(self) -> None:
        recovery = RECOVERY_DOC.read_text(encoding="utf-8")

        self.assertIn(
            "`[agents].max_concurrent_threads_per_session` setting is the maximum number of",
            recovery,
        )
        self.assertIn("concurrent agent threads outside the main Codex thread", recovery)
        self.assertIn(
            "machine-specific `~/.codex/config.toml`",
            recovery,
        )
        self.assertIn(
            "[agents]\nenabled = true\nmax_concurrent_threads_per_session = 8",
            recovery,
        )
        self.assertIn("total spawned-thread limit is `8`", recovery)
        self.assertIn(
            "must not create, copy, link, or automatically overwrite this file",
            recovery,
        )
        self.assertIn("Codex reads the", recovery)
        self.assertIn("setting only when a new task starts", recovery)

    def test_recovery_doc_documents_worker_acceptance_contract(self) -> None:
        recovery = RECOVERY_DOC.read_text(encoding="utf-8")

        self.assertIn("seven-field task contract", recovery)
        self.assertIn("structured response contract", recovery)
        self.assertIn("dispatch Flash", recovery)
        self.assertIn("one machine-readable", recovery)
        self.assertIn("Flash dispatches", recovery)

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
            flash = home / ".codex" / "agents" / "deepseek-v4-flash-worker.toml"
            self.assertTrue(flash.is_symlink())
            self.assertEqual(
                (ROOT / ".codex" / "agents" / "deepseek-v4-flash-worker.toml").resolve(),
                flash.resolve(),
            )
            self.assertEqual(EXPECTED_FLASH_CONFIG, flash.read_text(encoding="utf-8"))
            self.assertTrue((home / ".agents" / "skills" / "harness-engineering").is_symlink())
            self.assertTrue((home / ".agents" / "skills" / "web-access").is_symlink())
            self.assertIn("validation: index=skipped(custom-home)", first.stdout)
            self.assertIn("validation: doctor=skipped(custom-home)", first.stdout)

            second = self.run_setup(home, "install", "--profile", "daily")
            self.assertEqual(second.returncode, 0, second.stderr or second.stdout)
            self.assertIn("unchanged", second.stdout)
            self.assertIn(f"unchanged: {flash.parent.resolve() / flash.name}", second.stdout)

    def test_check_reports_missing_flash_agent_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            installed = self.run_setup(home, "install", "--profile", "core")
            self.assertEqual(installed.returncode, 0, installed.stderr or installed.stdout)

            flash = home / ".codex" / "agents" / "deepseek-v4-flash-worker.toml"
            flash.unlink()
            result = self.run_setup(home, "check", "--profile", "core")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(f"link: missing {flash.resolve()}", result.stderr)

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
            self.assertTrue((home / ".codex" / "agents" / "deepseek-v4-flash-worker.toml").is_symlink())
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

    def test_conflicting_flash_agent_is_backed_up_before_linking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            flash = home / ".codex" / "agents" / "deepseek-v4-flash-worker.toml"
            flash.parent.mkdir(parents=True)
            flash.write_text("user-owned\n", encoding="utf-8")

            result = self.run_setup(home, "install", "--profile", "core")

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertTrue(flash.is_symlink())
            self.assertEqual(EXPECTED_FLASH_CONFIG, flash.read_text(encoding="utf-8"))
            backups = self.find_backup_entries(
                home, Path(".codex/agents/deepseek-v4-flash-worker.toml")
            )
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
            self.assertIn(
                f"link: missing {home.resolve() / '.codex/agents/deepseek-v4-flash-worker.toml'}",
                missing.stderr,
            )

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
