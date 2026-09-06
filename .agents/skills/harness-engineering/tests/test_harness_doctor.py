from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "harness_doctor.py"
REPO_ROOT = Path(__file__).parents[4]
GLOBAL_AGENTS = REPO_ROOT / ".codex" / "AGENTS.md"
HARNESS_SKILL = Path(__file__).parents[1] / "SKILL.md"
HARNESS_WORKFLOW = REPO_ROOT / ".codex" / "docs" / "workflows" / "harness-engineering.md"
WORKTREE_WORKFLOW = REPO_ROOT / ".codex" / "docs" / "workflows" / "git-worktree.md"
GARDENING_WORKFLOW = REPO_ROOT / ".codex" / "docs" / "workflows" / "document-gardening.md"
WORKTREE_LEDGER_TEMPLATE = (
    Path(__file__).parents[1] / "assets" / "project-harness" / "worktree-ledger.md"
)
SPEC = importlib.util.spec_from_file_location("harness_doctor", MODULE_PATH)
doctor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(doctor)


def run(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        args,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def write_skill(root: Path, name: str, description: str, implicit: bool = True) -> None:
    skill = root / name
    (skill / "agents").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n",
        encoding="utf-8",
    )
    (skill / "agents" / "openai.yaml").write_text(
        "interface:\n"
        f'  display_name: "{name}"\n'
        f'  short_description: "Use {name} for deterministic checks"\n'
        f'  default_prompt: "Use ${name} for this task."\n'
        "policy:\n"
        f"  allow_implicit_invocation: {str(implicit).lower()}\n",
        encoding="utf-8",
    )


class SkillIndexTests(unittest.TestCase):
    def harness_skills(self, implicit: bool = True) -> list[dict]:
        return [
            {
                "name": name,
                "openai": (
                    {"policy": {"allow_implicit_invocation": implicit}}
                    if name == "harness-engineering"
                    else {}
                ),
            }
            for name in doctor.HARNESS_SKILLS
        ]

    def invocation_policy_errors(self, implicit: bool = True) -> list[dict]:
        with tempfile.TemporaryDirectory() as tmp:
            checks = doctor._harness_checks(Path(tmp), self.harness_skills(implicit))
        return [
            item
            for item in checks
            if item["code"] == "harness-skill-invocation-policy-mismatch"
        ]

    def test_requires_exact_core_five_skills(self) -> None:
        self.assertEqual(
            {
                "harness-engineering",
                "codebase-design",
                "diagnosing-bugs",
                "domain-modeling",
                "tdd",
            },
            doctor.HARNESS_SKILLS,
        )

        with tempfile.TemporaryDirectory() as tmp:
            checks = doctor._harness_checks(Path(tmp), self.harness_skills())

        missing = [item for item in checks if item["code"] == "harness-skill-missing"]
        self.assertEqual([], missing)

    def test_accepts_declared_harness_invocation_policy(self) -> None:
        self.assertEqual([], self.invocation_policy_errors())

    def test_rejects_harness_engineering_as_explicit_only(self) -> None:
        errors = self.invocation_policy_errors(False)

        self.assertEqual(["harness-engineering"], [item["details"]["skill"] for item in errors])
        self.assertTrue(errors[0]["details"]["expected"])

    def test_core_checks_require_integration_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)

            checks = doctor._harness_checks(home, [])
            missing_paths = {
                (item.get("details") or {}).get("path")
                for item in checks
                if item["code"] == "harness-path-missing"
            }

            expected = (
                home
                / ".agents"
                / "skills"
                / "harness-engineering"
                / "scripts"
                / "integration_preflight.py"
            )
            self.assertIn(str(expected), missing_paths)

    def test_core_checks_require_global_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)

            checks = doctor._harness_checks(home, self.harness_skills())
            missing_paths = {
                (item.get("details") or {}).get("path")
                for item in checks
                if item["code"] == "harness-path-missing"
            }

            self.assertIn(str(home / ".codex" / "AGENTS.md"), missing_paths)

    def test_worktree_ledger_tracks_browser_acceptance(self) -> None:
        content = WORKTREE_LEDGER_TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("Browser acceptance:", content)
        self.assertIn("not-applicable | pending | passed", content)


    def test_discovers_valid_skills_and_renders_stable_sorted_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            write_skill(root, "zeta", "Zeta description")
            write_skill(root, "alpha", "Alpha\n  description")

            skills, checks = doctor.discover_skills(root)
            rendered = doctor.render_skill_index(skills, root)

            self.assertFalse([item for item in checks if item["severity"] == "error"])
            self.assertLess(rendered.index("**alpha**"), rendered.index("**zeta**"))
            self.assertIn("有效 Skills 数量：2", rendered)
            self.assertNotIn("生成时间", rendered)
            self.assertIn("Alpha description", rendered)

    def test_rejects_name_mismatch_and_does_not_replace_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            write_skill(root, "folder-name", "Description")
            skill_md = root / "folder-name" / "SKILL.md"
            skill_md.write_text(
                skill_md.read_text(encoding="utf-8").replace(
                    "name: folder-name", "name: different-name"
                ),
                encoding="utf-8",
            )
            index = Path(tmp) / "skills-index.md"
            index.write_text("preserve me\n", encoding="utf-8")

            result = doctor.update_skill_index(root, index, write=True)

            self.assertEqual(1, result["exit_code"])
            self.assertEqual("preserve me\n", index.read_text(encoding="utf-8"))

    def test_atomic_index_write_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            write_skill(root, "alpha", "Alpha description")
            index = Path(tmp) / "skills-index.md"

            first = doctor.update_skill_index(root, index, write=True)
            before = index.read_bytes()
            second = doctor.update_skill_index(root, index, write=True)

            self.assertEqual(0, first["exit_code"])
            self.assertEqual(0, second["exit_code"])
            self.assertEqual(before, index.read_bytes())
            self.assertFalse(list(index.parent.glob(f".{index.name}.*.tmp")))

    def test_index_write_preserves_existing_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            write_skill(root, "alpha", "Alpha description")
            index = Path(tmp) / "skills-index.md"
            index.write_text("stale\n", encoding="utf-8")
            index.chmod(0o644)

            result = doctor.update_skill_index(root, index, write=True)

            self.assertEqual(0, result["exit_code"])
            self.assertEqual(0o644, index.stat().st_mode & 0o777)


class PolicyDocumentationTests(unittest.TestCase):
    def test_dirty_state_and_mechanical_conflicts_allow_safe_isolation(self) -> None:
        workflow = WORKTREE_WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("- Rebase or merge conflicts occur.", workflow)
        self.assertNotIn(
            "- The original worktree has uncommitted changes that might be touched by the task.",
            workflow,
        )
        self.assertIn("reconstruct only attributable, authorized task changes", workflow)
        self.assertIn("Resolve mechanical conflicts within the authorized task", workflow)
        self.assertIn("Never use conflict resolution to discard user changes", workflow)
        self.assertIn("bypass `STOP` or `MR_REQUIRED`", workflow)

    def test_mixed_file_commit_preserves_original_state(self) -> None:
        skill = (REPO_ROOT / ".agents/skills/git-auto-commit/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Do not use `git add -p` or stage a mixed file wholesale", skill)
        self.assertIn("reconstruct only those changes in a clean worktree", skill)
        self.assertIn("preserve the original working file", skill)
        self.assertIn("pre-existing staged boundary", skill)

    def test_harness_python_commands_use_uv(self) -> None:
        paths = (
            GLOBAL_AGENTS,
            HARNESS_SKILL,
            HARNESS_WORKFLOW,
            WORKTREE_WORKFLOW,
            GARDENING_WORKFLOW,
            REPO_ROOT / "README.md",
            REPO_ROOT / "README.en.md",
        )

        for path in paths:
            with self.subTest(path=path):
                content = path.read_text(encoding="utf-8")
                self.assertNotIn("python3 ~/.agents/skills/harness-engineering/", content)

    def test_worktree_workflow_resolves_symlink_targets_before_editing(self) -> None:
        content = WORKTREE_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("realpath", content)
        self.assertIn("real Git repository", content)

    def test_browser_acceptance_rule_does_not_block_browser_task_work(self) -> None:
        content = HARNESS_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("post-implementation acceptance", content)
        self.assertIn("web research", content)
        self.assertIn("authenticated web operations", content)

    def test_ego_browser_is_the_only_browser_workflow(self) -> None:
        retired_browser_skill = "web" + "-access"
        policy_paths = (
            GLOBAL_AGENTS,
            WORKTREE_WORKFLOW,
            REPO_ROOT / "README.md",
            REPO_ROOT / "README.en.md",
            REPO_ROOT / "THIRD_PARTY_NOTICES.md",
        )

        for path in policy_paths:
            with self.subTest(path=path):
                content = path.read_text(encoding="utf-8")
                self.assertNotIn(retired_browser_skill, content)

        global_rules = GLOBAL_AGENTS.read_text(encoding="utf-8")
        self.assertIn("`ego-browser`", global_rules)
        self.assertIn("`handOffTaskSpace`", global_rules)
        self.assertIn("`completeTaskSpace`", global_rules)
        self.assertFalse(
            (REPO_ROOT / ".agents" / "skills" / retired_browser_skill).exists()
        )

    def test_explicit_push_request_counts_as_browser_acceptance(self) -> None:
        # Entry points may link to the canonical rule instead of copying it.
        for path in (GLOBAL_AGENTS, HARNESS_SKILL):
            content = path.read_text(encoding="utf-8")
            self.assertIn("harness-engineering.md#browser-acceptance", content)
        for path in (HARNESS_WORKFLOW, WORKTREE_WORKFLOW):
            content = path.read_text(encoding="utf-8")
            self.assertIn("explicit current-task push request", content)
            self.assertIn("Do not ask separately", content)

        for path in (
            Path(__file__).parents[1] / "assets" / "project-harness" / "exec-plan.md",
            WORKTREE_LEDGER_TEMPLATE,
        ):
            with self.subTest(path=path):
                content = path.read_text(encoding="utf-8")
                self.assertIn("explicit push request", content)

    def test_high_confidence_auto_integration_policy(self) -> None:
        # Verify the complete authorization contract at its single owner.
        # Entry-point links are checked separately so missing routing still fails.
        for path in (GLOBAL_AGENTS, HARNESS_WORKFLOW):
            self.assertIn(
                "git-worktree.md#high-confidence-auto-integration",
                path.read_text(encoding="utf-8"),
            )
        self.assertIn("git-worktree.md", HARNESS_SKILL.read_text(encoding="utf-8"))

        for path in (
            Path(__file__).parents[1] / "assets" / "project-harness" / "exec-plan.md",
            WORKTREE_LEDGER_TEMPLATE,
        ):
            with self.subTest(path=path):
                content = path.read_text(encoding="utf-8")
                self.assertIn(
                    "not-applicable | pending | passed | waived-by-high-confidence",
                    content,
                )
                self.assertIn("High-confidence evidence:", content)

        expected_report = "浏览器验收：未执行；满足高置信度自动集成条件，按策略豁免"
        for path in (HARNESS_WORKFLOW,):
            with self.subTest(path=path):
                self.assertIn(expected_report, path.read_text(encoding="utf-8"))

        workflow = WORKTREE_WORKFLOW.read_text(encoding="utf-8")
        required_scenarios = (
            "UI or non-UI",
            "Every applicable test, lint, typecheck, build, and `git diff --check` passes",
            "Static final-diff review finds no issue",
            "`origin/dev`, `origin/develop`, `origin/test`, or `origin/uat`",
            "no project rule or current-task instruction prohibits pushing",
            "`DIRECT_FF`",
            "`REBASE_THEN_FF`",
            "`ALREADY_INTEGRATED`",
            "`MR_REQUIRED` is report-only",
            "production",
            "force-push",
            "Every applicable test",
            "critical non-browser check",
            "clean and current-task commits are fully isolated",
            "data-migration",
            "permission",
            "security-sensitive",
            "other-remote",
            "retains the task worktree",
        )
        for marker in required_scenarios:
            with self.subTest(scenario=marker):
                self.assertIn(marker, workflow)

    def test_global_rules_are_runtime_agnostic(self) -> None:
        content = GLOBAL_AGENTS.read_text(encoding="utf-8")

        self.assertNotIn("`question`", content)
        self.assertNotIn("DeepSeek", content)
        self.assertNotIn("opencode.db", content)
        self.assertIn("`request_user_input`", content)
        self.assertIn("native image input", content)


class WorktreeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "projects" / "sample"
        self.repo.mkdir(parents=True)
        run("git", "init", "-b", "main", cwd=self.repo)
        run("git", "config", "user.name", "Harness Test", cwd=self.repo)
        run("git", "config", "user.email", "harness@example.test", cwd=self.repo)
        (self.repo / "base.txt").write_text("base\n", encoding="utf-8")
        run("git", "add", "base.txt", cwd=self.repo)
        run("git", "commit", "-m", "base", cwd=self.repo)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def add_worktree(self, name: str, branch: str, *extra: str) -> Path:
        path = self.root / "worktrees" / name
        path.parent.mkdir(exist_ok=True)
        run(
            "git",
            "worktree",
            "add",
            *extra,
            "-b",
            branch,
            str(path),
            cwd=self.repo,
        )
        return path

    def test_classifies_worktrees_and_reports_ledger_coverage(self) -> None:
        ancestor = self.add_worktree("ancestor", "codex/ancestor")
        (self.repo / "main.txt").write_text("main\n", encoding="utf-8")
        run("git", "add", "main.txt", cwd=self.repo)
        run("git", "commit", "-m", "advance main", cwd=self.repo)

        unmerged = self.add_worktree("unmerged", "codex/unmerged")
        (unmerged / "feature.txt").write_text("feature\n", encoding="utf-8")
        run("git", "add", "feature.txt", cwd=unmerged)
        run("git", "commit", "-m", "feature", cwd=unmerged)

        dirty = self.add_worktree("dirty", "codex/dirty")
        (dirty / "dirty.txt").write_text("dirty\n", encoding="utf-8")

        detached = self.root / "worktrees" / "detached"
        run("git", "worktree", "add", "--detach", str(detached), cwd=self.repo)

        missing = self.add_worktree("missing", "codex/missing")
        shutil.rmtree(missing)

        ledger = self.repo / "docs" / "exec-plans" / "worktree-ledger.md"
        ledger.parent.mkdir(parents=True)
        ledger.write_text(f"Tracked: {unmerged}\n", encoding="utf-8")

        records, checks = doctor.scan_worktrees(
            [self.root / "projects"],
            now=datetime.now().astimezone() + timedelta(days=2),
        )
        states = {Path(item["path"]).name: item["state"] for item in records}
        coverage = {Path(item["path"]).name: item["ledger_covered"] for item in records}

        self.assertEqual("clean-ancestor", states[ancestor.name])
        self.assertEqual("clean-unmerged-or-rewritten", states[unmerged.name])
        self.assertEqual("dirty", states[dirty.name])
        self.assertEqual("detached", states[detached.name])
        self.assertEqual("missing-prunable", states[missing.name])
        self.assertTrue(coverage[unmerged.name])
        self.assertFalse(coverage[dirty.name])
        self.assertTrue(any(item["code"] == "worktree-ledger-missing" for item in checks))

    def test_linked_worktree_scan_resolves_main_repository_and_ledger(self) -> None:
        linked = self.add_worktree("linked", "codex/linked")
        (linked / "feature.txt").write_text("feature\n", encoding="utf-8")
        run("git", "add", "feature.txt", cwd=linked)
        run("git", "commit", "-m", "feature", cwd=linked)
        ledger = self.repo / "docs" / "exec-plans" / "worktree-ledger.md"
        ledger.parent.mkdir(parents=True)
        ledger.write_text("Tracked branch: codex/linked\n", encoding="utf-8")

        records, _ = doctor.scan_worktrees([linked])
        record = next(item for item in records if item["branch"] == "codex/linked")

        self.assertEqual(str(self.repo.resolve()), record["repo"])
        self.assertTrue(record["ledger_covered"])
        self.assertEqual(os.path.realpath(ledger), os.path.realpath(record["ledger_path"]))

    def test_scan_reports_activity_age_and_lifecycle(self) -> None:
        linked = self.add_worktree("age", "codex/age")
        now = datetime.now().astimezone()

        recent_records, _ = doctor.scan_worktrees(
            [self.root / "projects"],
            now=now,
        )
        stale_records, _ = doctor.scan_worktrees(
            [self.root / "projects"],
            now=now + timedelta(days=8),
        )

        recent = next(
            item
            for item in recent_records
            if os.path.realpath(item["path"]) == os.path.realpath(linked)
        )
        stale = next(
            item
            for item in stale_records
            if os.path.realpath(item["path"]) == os.path.realpath(linked)
        )
        self.assertEqual("active", recent["lifecycle"])
        self.assertEqual("stale", stale["lifecycle"])
        self.assertIn("last_activity_at", stale)
        self.assertGreater(stale["age_days"], 7)

    def test_cleanup_dry_run_preserves_eligible_worktree_and_branch(self) -> None:
        eligible = self.add_worktree("eligible-dry-run", "codex/eligible-dry-run")
        (self.repo / "main.txt").write_text("main\n", encoding="utf-8")
        run("git", "add", "main.txt", cwd=self.repo)
        run("git", "commit", "-m", "advance main", cwd=self.repo)

        records, checks = doctor.cleanup_worktrees(
            [self.root / "projects"],
            older_than_days=7,
            dry_run=True,
            now=datetime.now().astimezone() + timedelta(days=8),
            active_cwds=set(),
        )

        record = next(
            item
            for item in records
            if os.path.realpath(item["path"]) == os.path.realpath(eligible)
        )
        self.assertEqual("would-remove", record["cleanup_status"])
        self.assertTrue(eligible.exists())
        branches = run("git", "branch", "--format=%(refname:short)", cwd=self.repo)
        self.assertIn("codex/eligible-dry-run", branches.splitlines())
        self.assertFalse([item for item in checks if item["severity"] == "error"])

    def test_cleanup_removes_only_safe_old_codex_worktrees(self) -> None:
        eligible = self.add_worktree("eligible", "codex/eligible")
        ledgered = self.add_worktree("ledgered", "codex/ledgered")
        locked = self.add_worktree("locked", "codex/locked")
        active = self.add_worktree("active", "codex/active")
        manual = self.add_worktree("manual", "manual/merged")
        dirty = self.add_worktree("dirty-cleanup", "codex/dirty-cleanup")
        (dirty / "dirty.txt").write_text("dirty\n", encoding="utf-8")

        (self.repo / "main.txt").write_text("main\n", encoding="utf-8")
        run("git", "add", "main.txt", cwd=self.repo)
        run("git", "commit", "-m", "advance main", cwd=self.repo)
        run("git", "worktree", "lock", "--reason", "active task", str(locked), cwd=self.repo)

        ledger = self.repo / "docs" / "exec-plans" / "worktree-ledger.md"
        ledger.parent.mkdir(parents=True)
        ledger.write_text(f"Tracked: {ledgered}\n", encoding="utf-8")

        records, checks = doctor.cleanup_worktrees(
            [self.root / "projects"],
            older_than_days=7,
            dry_run=False,
            now=datetime.now().astimezone() + timedelta(days=8),
            active_cwds={active},
        )

        status_by_name = {
            Path(item["path"]).name: item["cleanup_status"]
            for item in records
            if item.get("path")
        }
        self.assertEqual("removed", status_by_name[eligible.name])
        self.assertEqual("ledger-covered", status_by_name[ledgered.name])
        self.assertEqual("locked", status_by_name[locked.name])
        self.assertEqual("active-process", status_by_name[active.name])
        self.assertEqual("non-codex-branch", status_by_name[manual.name])
        self.assertEqual("unsafe-state", status_by_name[dirty.name])
        self.assertFalse(eligible.exists())
        for preserved in (ledgered, locked, active, manual, dirty):
            self.assertTrue(preserved.exists())
        branches = run("git", "branch", "--format=%(refname:short)", cwd=self.repo)
        self.assertNotIn("codex/eligible", branches.splitlines())
        self.assertFalse([item for item in checks if item["severity"] == "error"])

    def test_cleanup_fails_closed_when_active_process_scan_is_unavailable(self) -> None:
        eligible = self.add_worktree("eligible-no-lsof", "codex/eligible-no-lsof")
        (self.repo / "main.txt").write_text("main\n", encoding="utf-8")
        run("git", "add", "main.txt", cwd=self.repo)
        run("git", "commit", "-m", "advance main", cwd=self.repo)
        original = doctor._active_process_cwds

        def fail_active_scan():
            raise RuntimeError("lsof failed")

        doctor._active_process_cwds = fail_active_scan
        try:
            records, checks = doctor.cleanup_worktrees(
                [self.root / "projects"],
                older_than_days=7,
                dry_run=False,
                now=datetime.now().astimezone() + timedelta(days=8),
            )
        finally:
            doctor._active_process_cwds = original

        record = next(item for item in records if item["branch"] == "codex/eligible-no-lsof")
        self.assertEqual("active-check-unavailable", record["cleanup_status"])
        self.assertTrue(eligible.exists())
        self.assertTrue(any(item["code"] == "worktree-active-check-failed" for item in checks))

    def test_cleanup_preserves_missing_worktree_metadata(self) -> None:
        missing = self.add_worktree("missing-cleanup", "codex/missing-cleanup")
        shutil.rmtree(missing)

        records, _ = doctor.cleanup_worktrees(
            [self.root / "projects"],
            older_than_days=7,
            dry_run=False,
            now=datetime.now().astimezone() + timedelta(days=8),
            active_cwds=set(),
        )

        record = next(item for item in records if item["branch"] == "codex/missing-cleanup")
        self.assertEqual("unsafe-state", record["cleanup_status"])
        listing = run("git", "worktree", "list", "--porcelain", cwd=self.repo)
        self.assertIn(os.path.realpath(missing), listing)


class DocumentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "sample"
        self.repo.mkdir()
        run("git", "init", "-b", "main", cwd=self.repo)
        run("git", "config", "user.name", "Harness Test", cwd=self.repo)
        run("git", "config", "user.email", "harness@example.test", cwd=self.repo)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def commit(self, *paths: str) -> None:
        run("git", "add", *paths, cwd=self.repo)
        run("git", "commit", "-m", "docs", cwd=self.repo)

    def test_reports_missing_local_links_and_ignores_external_urls(self) -> None:
        docs = self.repo / "docs"
        docs.mkdir()
        (docs / "existing.md").write_text("# Existing\n", encoding="utf-8")
        (self.repo / "README.md").write_text(
            "[existing](docs/existing.md)\n"
            "[missing](docs/missing.md)\n"
            "[external](https://example.com/docs)\n"
            "```markdown\n[example](docs/example-only.md)\n```\n",
            encoding="utf-8",
        )
        self.commit("README.md", "docs/existing.md")

        audit, checks = doctor.scan_documents(
            [self.repo],
            memory_root=self.root / "no-memory",
        )

        missing = [item for item in checks if item["code"] == "docs-local-link-missing"]
        self.assertEqual(1, len(missing))
        self.assertEqual(1, audit["repositories"])
        self.assertEqual(2, audit["markdown_files"])

    def test_reports_large_agents_and_old_open_execution_plan(self) -> None:
        agents = self.repo / "AGENTS.md"
        agents.write_text("\n".join(f"rule {index}" for index in range(121)) + "\n")
        plan = self.repo / "docs" / "exec-plans" / "old-plan.md"
        plan.parent.mkdir(parents=True)
        plan.write_text("# Plan\n\n- [ ] unfinished\n", encoding="utf-8")
        self.commit("AGENTS.md", "docs/exec-plans/old-plan.md")

        audit, checks = doctor.scan_documents(
            [self.repo],
            memory_root=self.root / "no-memory",
            now=datetime.now().astimezone() + timedelta(days=31),
        )

        codes = {item["code"] for item in checks}
        self.assertIn("docs-agents-too-long", codes)
        self.assertIn("docs-exec-plan-stale-open", codes)
        self.assertEqual(1, audit["large_agents_files"])
        self.assertEqual(1, audit["stale_open_plans"])

    def test_validates_new_and_legacy_engineering_rule_verification(self) -> None:
        rules = self.repo / "docs" / "engineering-rules"
        rules.mkdir(parents=True)
        (rules / "automated.md").write_text(
            "# Automated\n\n## Verification\n\n"
            "- Mode: automated\n- Command: `npm test`\n",
            encoding="utf-8",
        )
        (rules / "manual.md").write_text(
            "# Manual\n\n## Verification\n\n"
            "- Mode: manual\n- Command: n/a\n- Reason: Requires visual inspection.\n",
            encoding="utf-8",
        )
        (rules / "legacy.md").write_text(
            "# Legacy\n\n## Verification\n\n```bash\nmake verify\n```\n",
            encoding="utf-8",
        )
        (rules / "invalid.md").write_text(
            "# Invalid\n\n## Verification\n\n- Mode: manual\n- Command: n/a\n",
            encoding="utf-8",
        )
        (rules / "missing.md").write_text("# Missing\n", encoding="utf-8")
        self.commit("docs/engineering-rules")

        audit, checks = doctor.scan_documents(
            [self.repo],
            memory_root=self.root / "no-memory",
        )

        verification = [
            item for item in checks if item["code"].startswith("docs-rule-verification")
        ]
        self.assertEqual(2, len(verification))
        self.assertEqual(5, audit["engineering_rules"])
        self.assertEqual(2, audit["rules_needing_verification"])

    def test_reports_memory_size_without_modifying_memory(self) -> None:
        memory = self.root / "memory"
        memory.mkdir()
        summary = memory / "memory_summary.md"
        full = memory / "MEMORY.md"
        summary.write_text("line\n" * 301, encoding="utf-8")
        full.write_text("line\n" * 1001, encoding="utf-8")

        audit, checks = doctor.scan_documents([self.repo], memory_root=memory)

        self.assertEqual(301, audit["memory"]["memory_summary.md"]["lines"])
        self.assertEqual(1001, audit["memory"]["MEMORY.md"]["lines"])
        self.assertEqual(2, len([item for item in checks if item["code"] == "docs-memory-large"]))
        self.assertEqual("line\n" * 301, summary.read_text(encoding="utf-8"))

    def test_explicit_linked_worktree_scans_that_worktree(self) -> None:
        base = self.repo / "base.txt"
        base.write_text("base\n", encoding="utf-8")
        self.commit("base.txt")
        linked = self.root / "linked"
        run("git", "worktree", "add", "-b", "codex/docs", str(linked), cwd=self.repo)
        (linked / "README.md").write_text("[missing](linked-only.md)\n", encoding="utf-8")
        run("git", "add", "README.md", cwd=linked)
        run("git", "commit", "-m", "linked docs", cwd=linked)

        audit, checks = doctor.scan_documents(
            [linked],
            memory_root=self.root / "no-memory",
        )

        self.assertEqual([str(linked.resolve())], audit["repository_paths"])
        missing = next(item for item in checks if item["code"] == "docs-local-link-missing")
        self.assertEqual(str(linked.resolve()), missing["details"]["repo"])

    def test_parent_scan_deduplicates_linked_worktrees_by_common_directory(self) -> None:
        base = self.repo / "README.md"
        base.write_text("# Main\n", encoding="utf-8")
        self.commit("README.md")
        linked = self.root / "linked"
        run("git", "worktree", "add", "-b", "codex/docs", str(linked), cwd=self.repo)

        audit, _ = doctor.scan_documents(
            [self.root],
            memory_root=self.root / "no-memory",
        )

        self.assertEqual(1, audit["repositories"])
        self.assertEqual(1, len(audit["repository_paths"]))


class ReportTests(unittest.TestCase):
    def test_json_contract_and_exit_codes(self) -> None:
        report = doctor.make_report(
            checks=[
                doctor.check("warning", "sample-warning", "warning", section="skills"),
            ],
            worktrees=[],
            docs_audit={"repositories": 0, "markdown_files": 0},
        )

        payload = json.loads(doctor.render_report(report, "json"))

        self.assertEqual(doctor.REPORT_VERSION, payload["version"])
        self.assertEqual({"errors": 0, "warnings": 1, "ok": 0}, payload["summary"])
        self.assertIn("skills", payload["section_summaries"])
        self.assertIn("worktrees", payload["section_summaries"])
        self.assertNotIn("docs", payload["section_summaries"])
        self.assertEqual(10, payload["version"])
        self.assertEqual(0, doctor.report_exit_code(report, strict=False))
        self.assertEqual(1, doctor.report_exit_code(report, strict=True))

    def test_errors_fail_without_strict_mode(self) -> None:
        report = doctor.make_report(
            checks=[doctor.check("error", "sample-error", "error")],
            worktrees=[],
        )
        self.assertEqual(1, doctor.report_exit_code(report, strict=False))

    def test_core_report_omits_full_scan_sections(self) -> None:
        report = doctor.make_report(
            checks=[doctor.check("ok", "core", "core passed")],
            worktrees=[],
            scope="core",
        )

        rendered = doctor.render_report(report, "human")

        self.assertIn("Harness Doctor (core)", rendered)
        self.assertNotIn("Session capture markers", rendered)
        self.assertNotIn("Worktrees inspected", rendered)

    def test_full_report_groups_sections(self) -> None:
        report = doctor.make_report(
            checks=[
                doctor.check("ok", "skills-ok", "skills", section="skills"),
                doctor.check("warning", "worktree-old", "worktree", section="worktrees"),
            ],
            worktrees=[{"state": "clean-ancestor", "lifecycle": "stale"}],
        )

        rendered = doctor.render_report(report, "human")

        self.assertIn("[Skills]", rendered)
        self.assertIn("[Worktrees]", rendered)

    def test_docs_section_is_explicit_and_rendered(self) -> None:
        parser = doctor.build_parser()
        parsed = parser.parse_args(
            ["doctor", "--full", "--section", "docs", "--repo-root", "/tmp/repo"]
        )
        report = doctor.make_report(
            checks=[doctor.check("warning", "docs-sample", "docs", section="docs")],
            worktrees=[],
            docs_audit={"repositories": 1, "markdown_files": 2},
            sections=["docs"],
        )

        rendered = doctor.render_report(report, "human")
        payload = json.loads(doctor.render_report(report, "json"))

        self.assertEqual(["docs"], parsed.section)
        self.assertIn("[Docs]", rendered)
        self.assertIn("repositories=1 markdown_files=2", rendered)
        self.assertEqual(1, payload["docs_audit"]["repositories"])

    def test_doctor_full_flag_is_opt_in(self) -> None:
        parser = doctor.build_parser()

        self.assertFalse(parser.parse_args(["doctor"]).full)
        self.assertTrue(parser.parse_args(["doctor", "--full"]).full)
        parsed = parser.parse_args(
            ["doctor", "--full", "--section", "worktrees", "--section", "docs"]
        )
        self.assertEqual(["worktrees", "docs"], parsed.section)

    def test_default_repo_roots_only_uses_current_git_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            run("git", "init", "-q", cwd=repo)
            nested = repo / "nested"
            nested.mkdir()
            previous = Path.cwd()
            try:
                os.chdir(nested)
                roots = doctor._default_repo_roots(Path(tmp) / "home")
            finally:
                os.chdir(previous)

        self.assertEqual([repo.resolve()], roots)

    def test_cleanup_command_requires_safe_flag(self) -> None:
        parser = doctor.build_parser()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parser.parse_args(["cleanup"])
        parsed = parser.parse_args(["cleanup", "--safe", "--dry-run"])
        self.assertEqual(7, parsed.older_than_days)
        self.assertTrue(parsed.dry_run)

    def test_main_returns_two_for_runtime_environment_errors(self) -> None:
        original = doctor._doctor_command

        def fail(_args):
            raise RuntimeError("environment failed")

        doctor._doctor_command = fail
        try:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                exit_code = doctor.main(["doctor", "--full"])
        finally:
            doctor._doctor_command = original

        self.assertEqual(2, exit_code)
        self.assertIn("ERROR: environment failed", stderr.getvalue())

if __name__ == "__main__":
    unittest.main()
