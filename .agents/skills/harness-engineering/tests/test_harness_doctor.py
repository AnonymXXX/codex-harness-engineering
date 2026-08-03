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


class SessionAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.now = datetime.now().astimezone()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def stamp(self, value: datetime) -> str:
        return value.isoformat()

    def event(self, value: datetime, event_type: str, payload: dict) -> dict:
        return {"timestamp": self.stamp(value), "type": event_type, "payload": payload}

    def metadata(self, value: datetime, session_id: str, *, parent: str | None = None, depth: int = 0) -> dict:
        source = {}
        if parent:
            source = {
                "subagent": {
                    "thread_spawn": {
                        "agent_role": "luna_worker",
                        "parent_thread_id": parent,
                        "depth": depth,
                    }
                }
            }
        return {
            "timestamp": self.stamp(value),
            "type": "session_meta",
            "payload": {"id": session_id, "source": source},
        }

    def write(self, path: Path, rows: list[dict | str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [row if isinstance(row, str) else json.dumps(row, ensure_ascii=False) for row in rows]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_direct_completion_uses_filename_id_and_deduplicates_corrupt_stale_records(self) -> None:
        root_id = "11111111-1111-1111-1111-111111111111"
        child_id = "22222222-2222-2222-2222-222222222222"
        root_path = self.root / f"rollout-2026-08-03T00-00-00-{root_id}.jsonl"
        child_path = self.root / f"rollout-2026-08-03T00-00-00-{child_id}.jsonl"
        duplicate_path = self.root / "copy" / child_path.name
        spawn = {
            "type": "function_call",
            "name": "spawn_agent",
            "call_id": "call-child",
            "arguments": json.dumps({"agent_type": "luna_worker"}),
            "turn_id": "root-turn",
        }
        root_rows = [
            self.metadata(self.now, root_id),
            {"timestamp": self.stamp(self.now), "type": "response_item", "payload": spawn},
            self.event(
                self.now,
                "event_msg",
                {
                    "type": "sub_agent_activity",
                    "event_id": "call-child",
                    "agent_thread_id": child_id,
                    "kind": "started",
                },
            ),
            self.event(
                self.now,
                "event_msg",
                {"type": "task_complete", "turn_id": "root-turn", "last_agent_message": "完成"},
            ),
            self.event(
                self.now - timedelta(days=30),
                "event_msg",
                {"type": "task_complete", "turn_id": "stale-turn", "last_agent_message": "过期"},
            ),
        ]
        child_rows = [
            self.metadata(self.now, "wrong-payload-id", parent=root_id, depth=1),
            self.event(
                self.now + timedelta(seconds=1),
                "event_msg",
                {"type": "task_complete", "turn_id": "child-turn", "last_agent_message": "规则沉淀：完成"},
            ),
            "{not-json",
        ]
        self.write(root_path, root_rows)
        self.write(child_path, child_rows)
        self.write(duplicate_path, child_rows[:2])

        audit = doctor.audit_sessions(self.root, 7)

        self.assertEqual(3, audit["raw_completed"])
        self.assertEqual(2, audit["completed"])
        self.assertEqual(1, audit["duplicates_skipped"])
        self.assertEqual(1, audit["reports"])
        self.assertEqual(1, audit["root_completed"])
        self.assertEqual(1, audit["luna_started"])
        self.assertEqual(1, audit["luna_completed"])
        self.assertEqual(0, audit["luna_interrupted"])
        self.assertEqual(1, audit["luna_peak_concurrency"])
        self.assertEqual(1, audit["root_turns_with_luna"])
        self.assertEqual(1, audit["successful_root_turns_with_luna"])
        self.assertEqual(1, audit["root_turns_missing_luna_outcome_report"])

    def test_luna_outcome_report_counts_reused_units_and_duplicate_rollouts(self) -> None:
        root_id = "33333333-3333-3333-3333-333333333333"
        child_id = "44444444-4444-4444-4444-444444444444"
        root_path = self.root / f"rollout-2026-08-03T00-00-00-{root_id}.jsonl"
        duplicate_path = self.root / "copy" / root_path.name
        root_rows = [
            self.metadata(self.now, root_id),
            self.event(
                self.now,
                "event_msg",
                {
                    "type": "sub_agent_activity",
                    "agent_thread_id": child_id,
                    "kind": "started",
                    "turn_id": "root-turn",
                },
            ),
            self.event(
                self.now + timedelta(seconds=2),
                "event_msg",
                {
                    "type": "task_complete",
                    "turn_id": "root-turn",
                    "last_agent_message": (
                        "完成\n\nLuna 验收：adopted=2 partial=1 rejected=1 failed=1"
                    ),
                },
            ),
        ]
        self.write(root_path, root_rows)
        self.write(duplicate_path, root_rows)
        self.write(
            self.root / f"rollout-2026-08-03T00-00-01-{child_id}.jsonl",
            [
                self.metadata(self.now, child_id, parent=root_id, depth=1),
                self.event(
                    self.now + timedelta(seconds=1),
                    "event_msg",
                    {"type": "task_complete", "turn_id": "child-turn"},
                ),
            ],
        )

        audit = doctor.audit_sessions(self.root, 7)

        self.assertEqual(1, audit["root_turns_with_luna_outcome_report"])
        self.assertEqual(5, audit["luna_units_reported"])
        self.assertEqual(2, audit["luna_units_adopted"])
        self.assertEqual(1, audit["luna_units_partially_adopted"])
        self.assertEqual(1, audit["luna_units_rejected"])
        self.assertEqual(1, audit["luna_units_failed"])
        self.assertEqual(0, audit["root_turns_missing_luna_outcome_report"])
        self.assertEqual(0, audit["luna_outcome_reports_invalid"])

    def test_zero_luna_outcome_report_is_valid(self) -> None:
        root_id, child_id = "root-zero", "child-zero"
        self.write(
            self.root / "root-zero.jsonl",
            [
                self.metadata(self.now, root_id),
                self.event(
                    self.now,
                    "event_msg",
                    {
                        "type": "sub_agent_activity",
                        "agent_thread_id": child_id,
                        "kind": "started",
                        "turn_id": "root-turn",
                    },
                ),
                self.event(
                    self.now + timedelta(seconds=2),
                    "event_msg",
                    {
                        "type": "task_complete",
                        "turn_id": "root-turn",
                        "last_agent_message": (
                            "Luna 验收：adopted=0 partial=0 rejected=0 failed=0"
                        ),
                    },
                ),
            ],
        )
        self.write(
            self.root / "child-zero.jsonl",
            [
                self.metadata(self.now, child_id, parent=root_id, depth=1),
                self.event(
                    self.now + timedelta(seconds=1),
                    "event_msg",
                    {"type": "turn_aborted", "turn_id": "child-turn"},
                ),
            ],
        )

        audit = doctor.audit_sessions(self.root, 7)

        self.assertEqual(1, audit["root_turns_with_luna_outcome_report"])
        self.assertEqual(0, audit["luna_units_reported"])
        self.assertEqual(0, audit["root_turns_missing_luna_outcome_report"])
        self.assertEqual(0, audit["luna_outcome_reports_invalid"])

    def test_malformed_multiple_and_orphan_luna_outcomes_are_invalid(self) -> None:
        malformed_status, _ = doctor._audit_luna_outcome(
            ["Luna 验收：adopted=-1 partial=0 rejected=0 failed=0"]
        )
        repeated_status, _ = doctor._audit_luna_outcome(
            [
                "Luna 验收：adopted=1 partial=0 rejected=0 failed=0\n"
                "Luna 验收：adopted=1 partial=0 rejected=0 failed=0"
            ]
        )
        self.assertEqual("invalid", malformed_status)
        self.assertEqual("invalid", repeated_status)

        root_id, child_id = "root-invalid", "child-invalid"
        self.write(
            self.root / "root-invalid.jsonl",
            [
                self.metadata(self.now, root_id),
                self.event(
                    self.now,
                    "event_msg",
                    {
                        "type": "sub_agent_activity",
                        "agent_thread_id": child_id,
                        "kind": "started",
                        "turn_id": "root-turn",
                    },
                ),
                self.event(
                    self.now + timedelta(seconds=2),
                    "event_msg",
                    {
                        "type": "task_complete",
                        "turn_id": "root-turn",
                        "last_agent_message": (
                            "Luna 验收：adopted=1 partial=0 rejected=0 failed=0\n"
                            "Luna 验收：adopted=0 partial=1 rejected=0 failed=0"
                        ),
                    },
                ),
            ],
        )
        self.write(
            self.root / "child-invalid.jsonl",
            [
                self.metadata(self.now, child_id, parent=root_id, depth=1),
                self.event(
                    self.now + timedelta(seconds=1),
                    "event_msg",
                    {"type": "task_complete", "turn_id": "child-turn"},
                ),
            ],
        )
        self.write(
            self.root / "orphan.jsonl",
            [
                self.metadata(self.now, "orphan-root"),
                self.event(
                    self.now + timedelta(seconds=3),
                    "event_msg",
                    {
                        "type": "task_complete",
                        "turn_id": "orphan-turn",
                        "last_agent_message": (
                            "Luna 验收：adopted=1 partial=0 rejected=0 failed=0"
                        ),
                    },
                ),
            ],
        )

        audit = doctor.audit_sessions(self.root, 7)

        self.assertEqual(0, audit["root_turns_with_luna_outcome_report"])
        self.assertEqual(2, audit["luna_outcome_reports_invalid"])
        self.assertEqual(0, audit["root_turns_missing_luna_outcome_report"])

    def test_interrupted_luna_is_session_deduplicated_and_not_successful(self) -> None:
        root_id = "root-interrupted"
        child_id = "child-interrupted"
        root_path = self.root / "root.jsonl"
        child_path = self.root / "child.jsonl"
        self.write(
            root_path,
            [
                self.metadata(self.now, root_id),
                self.event(
                    self.now,
                    "event_msg",
                    {
                        "type": "sub_agent_activity",
                        "event_id": "call-interrupted",
                        "agent_thread_id": child_id,
                        "kind": "started",
                        "turn_id": "root-turn",
                    },
                ),
                self.event(
                    self.now + timedelta(seconds=2),
                    "event_msg",
                    {"type": "task_complete", "turn_id": "root-turn", "last_agent_message": "主任务"},
                ),
            ],
        )
        self.write(
            child_path,
            [
                self.metadata(self.now, child_id, parent=root_id, depth=1),
                self.event(
                    self.now + timedelta(seconds=1),
                    "event_msg",
                    {"type": "turn_aborted", "turn_id": "child-turn"},
                ),
                self.event(
                    self.now + timedelta(seconds=1),
                    "event_msg",
                    {"type": "turn_aborted", "turn_id": "child-turn"},
                ),
            ],
        )

        audit = doctor.audit_sessions(self.root, 7)

        self.assertEqual(1, audit["luna_started"])
        self.assertEqual(0, audit["luna_completed"])
        self.assertEqual(1, audit["luna_interrupted"])
        self.assertEqual(1, audit["root_turns_with_luna"])
        self.assertEqual(0, audit["successful_root_turns_with_luna"])

    def test_nested_workers_and_peak_concurrency(self) -> None:
        root_id, child_one, child_two, nested = "root", "child-one", "child-two", "nested"
        base = self.now
        root_rows = [
            self.metadata(base, root_id),
            self.event(
                base,
                "event_msg",
                {
                    "type": "sub_agent_activity",
                    "event_id": "call-one",
                    "agent_thread_id": child_one,
                    "kind": "started",
                    "turn_id": "root-turn",
                },
            ),
            self.event(
                base + timedelta(seconds=1),
                "event_msg",
                {
                    "type": "sub_agent_activity",
                    "event_id": "call-two",
                    "agent_thread_id": child_two,
                    "kind": "started",
                    "turn_id": "root-turn",
                },
            ),
            self.event(
                base + timedelta(seconds=8),
                "event_msg",
                {"type": "task_complete", "turn_id": "root-turn", "last_agent_message": "完成"},
            ),
        ]
        child_one_rows = [
            self.metadata(base, child_one, parent=root_id, depth=1),
            self.event(base + timedelta(seconds=2), "event_msg", {"type": "sub_agent_activity", "agent_thread_id": nested, "kind": "started"}),
            self.event(base + timedelta(seconds=5), "event_msg", {"type": "task_complete", "turn_id": "one-turn"}),
        ]
        child_two_rows = [
            self.metadata(base + timedelta(seconds=1), child_two, parent=root_id, depth=1),
            self.event(base + timedelta(seconds=6), "event_msg", {"type": "task_complete", "turn_id": "two-turn"}),
        ]
        nested_rows = [
            self.metadata(base + timedelta(seconds=2), nested, parent=child_one, depth=2),
            self.event(base + timedelta(seconds=7), "event_msg", {"type": "task_complete", "turn_id": "nested-turn"}),
        ]
        self.write(self.root / "root.jsonl", root_rows)
        self.write(self.root / "child-one.jsonl", child_one_rows)
        self.write(self.root / "child-two.jsonl", child_two_rows)
        self.write(self.root / "nested.jsonl", nested_rows)

        audit = doctor.audit_sessions(self.root, 7)

        self.assertEqual(3, audit["luna_started"])
        self.assertEqual(3, audit["luna_completed"])
        self.assertEqual(1, audit["luna_nested"])
        self.assertEqual(3, audit["luna_peak_concurrency"])
        self.assertEqual(1, audit["root_turns_with_luna"])
        self.assertEqual(1, audit["successful_root_turns_with_luna"])

    def test_root_completed_excludes_non_luna_subagent_sessions(self) -> None:
        root_id, worker_id = "root-only", "explorer-child"
        worker_meta = {
            "timestamp": self.stamp(self.now),
            "type": "session_meta",
            "payload": {
                "id": worker_id,
                "source": {
                    "subagent": {
                        "thread_spawn": {
                            "agent_role": "explorer",
                            "parent_thread_id": root_id,
                            "depth": 1,
                        }
                    }
                },
            },
        }
        self.write(
            self.root / "root.jsonl",
            [
                self.metadata(self.now, root_id),
                self.event(
                    self.now,
                    "event_msg",
                    {"type": "task_complete", "turn_id": "root-turn", "last_agent_message": "root"},
                ),
            ],
        )
        self.write(
            self.root / "explorer.jsonl",
            [
                worker_meta,
                self.event(
                    self.now,
                    "event_msg",
                    {"type": "task_complete", "turn_id": "worker-turn", "last_agent_message": "worker"},
                ),
            ],
        )

        audit = doctor.audit_sessions(self.root, 7)

        self.assertEqual(2, audit["raw_completed"])
        self.assertEqual(2, audit["completed"])
        self.assertEqual(1, audit["root_completed"])

    def test_completed_keeps_global_turn_id_deduplication(self) -> None:
        root_id, child_id = "root-shared", "luna-shared"
        self.write(
            self.root / "root.jsonl",
            [
                self.metadata(self.now, root_id),
                self.event(
                    self.now,
                    "event_msg",
                    {"type": "task_complete", "turn_id": "shared-turn", "last_agent_message": "root"},
                ),
            ],
        )
        self.write(
            self.root / "child.jsonl",
            [
                self.metadata(self.now, child_id, parent=root_id, depth=1),
                self.event(
                    self.now,
                    "event_msg",
                    {"type": "task_complete", "turn_id": "shared-turn", "last_agent_message": "child"},
                ),
            ],
        )

        audit = doctor.audit_sessions(self.root, 7)

        self.assertEqual(2, audit["raw_completed"])
        self.assertEqual(1, audit["completed"])
        self.assertEqual(1, audit["duplicates_skipped"])
        self.assertEqual(1, audit["root_completed"])
        self.assertEqual(1, audit["luna_completed"])

    def test_filename_identity_deduplicates_metadata_free_partial_copy(self) -> None:
        root_id = "33333333-3333-3333-3333-333333333333"
        child_id = "44444444-4444-4444-4444-444444444444"
        root_path = self.root / f"rollout-2026-08-03T00-00-00-{root_id}.jsonl"
        child_path = self.root / f"rollout-2026-08-03T00-00-00-{child_id}.jsonl"
        partial_copy = self.root / "partial" / child_path.name
        self.write(
            root_path,
            [
                self.metadata(self.now, root_id),
                self.event(
                    self.now,
                    "event_msg",
                    {"type": "task_complete", "turn_id": "root-turn", "last_agent_message": "root"},
                ),
            ],
        )
        self.write(
            child_path,
            [
                self.metadata(self.now, child_id, parent=root_id, depth=1),
                self.event(
                    self.now,
                    "event_msg",
                    {"type": "task_complete", "turn_id": "child-turn", "last_agent_message": "child"},
                ),
            ],
        )
        self.write(
            partial_copy,
            [
                "{truncated-before-session-meta",
                self.event(
                    self.now,
                    "event_msg",
                    {"type": "task_complete", "turn_id": "child-turn", "last_agent_message": "child copy"},
                ),
            ],
        )

        audit = doctor.audit_sessions(self.root, 7)

        self.assertEqual(3, audit["raw_completed"])
        self.assertEqual(2, audit["completed"])
        self.assertEqual(1, audit["duplicates_skipped"])
        self.assertEqual(1, audit["root_completed"])
        self.assertEqual(1, audit["luna_started"])
        self.assertEqual(1, audit["luna_completed"])

    def test_failed_spawn_output_does_not_create_provisional_luna(self) -> None:
        root_id = "root-limit"
        rows = [self.metadata(self.now, root_id)]
        for index in range(6):
            call_id = f"call-{index}"
            rows.append(
                {
                    "timestamp": self.stamp(self.now),
                    "type": "response_item",
                    "payload": {
                        "type": "function_call",
                        "name": "spawn_agent",
                        "call_id": call_id,
                        "arguments": json.dumps({"agent_type": "luna_worker"}),
                        "turn_id": "root-turn",
                    },
                }
            )
            output = (
                "collab spawn failed: agent thread limit reached"
                if index == 5
                else json.dumps({"task_name": f"/root/luna-{index}"})
            )
            rows.append(
                {
                    "timestamp": self.stamp(self.now),
                    "type": "response_item",
                    "payload": {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": output,
                    },
                }
            )
        rows.append(
            self.event(
                self.now + timedelta(seconds=1),
                "event_msg",
                {"type": "task_complete", "turn_id": "root-turn", "last_agent_message": "root"},
            )
        )
        self.write(self.root / "root.jsonl", rows)

        audit = doctor.audit_sessions(self.root, 7)

        self.assertEqual(5, audit["luna_started"])
        self.assertEqual(5, audit["luna_peak_concurrency"])
        self.assertEqual(1, audit["root_turns_with_luna"])
        self.assertEqual(0, audit["luna_completed"])
        self.assertEqual(0, audit["successful_root_turns_with_luna"])

    def test_failed_spawn_does_not_filter_independent_metadata_children(self) -> None:
        root_id = "root-real-children"
        rows = [self.metadata(self.now, root_id)]
        child_rows: list[tuple[str, list[dict]]] = []
        for index in range(5):
            child_id = f"real-child-{index}"
            call_id = f"real-call-{index}"
            rows.append(
                {
                    "timestamp": self.stamp(self.now),
                    "type": "response_item",
                    "payload": {
                        "type": "function_call",
                        "name": "spawn_agent",
                        "call_id": call_id,
                        "arguments": json.dumps({"agent_type": "luna_worker"}),
                        "turn_id": "root-turn",
                    },
                }
            )
            rows.append(
                {
                    "timestamp": self.stamp(self.now),
                    "type": "response_item",
                    "payload": {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": json.dumps({"task_name": f"/root/{child_id}"}),
                    },
                }
            )
            child_rows.append(
                (
                    child_id,
                    [
                        self.metadata(self.now, child_id, parent=root_id, depth=1),
                        self.event(
                            self.now + timedelta(seconds=1),
                            "event_msg",
                            {"type": "task_complete", "turn_id": f"child-turn-{index}"},
                        ),
                    ],
                )
            )
        rows.extend(
            [
                {
                    "timestamp": self.stamp(self.now),
                    "type": "response_item",
                    "payload": {
                        "type": "function_call",
                        "name": "spawn_agent",
                        "call_id": "failed-real-call",
                        "arguments": json.dumps({"agent_type": "luna_worker"}),
                        "turn_id": "root-turn",
                    },
                },
                {
                    "timestamp": self.stamp(self.now),
                    "type": "response_item",
                    "payload": {
                        "type": "function_call_output",
                        "call_id": "failed-real-call",
                        "output": "collab spawn failed: agent thread limit reached",
                    },
                },
                self.event(
                    self.now + timedelta(seconds=2),
                    "event_msg",
                    {"type": "task_complete", "turn_id": "root-turn", "last_agent_message": "root"},
                ),
            ]
        )
        self.write(self.root / "root.jsonl", rows)
        for child_id, child_data in child_rows:
            self.write(self.root / f"{child_id}.jsonl", child_data)

        audit = doctor.audit_sessions(self.root, 7)

        self.assertEqual(5, audit["luna_started"])
        self.assertEqual(5, audit["luna_completed"])
        self.assertEqual(5, audit["luna_peak_concurrency"])
        self.assertEqual(1, audit["root_turns_with_luna"])
        self.assertEqual(1, audit["successful_root_turns_with_luna"])

    def test_luna_spawned_by_non_luna_subagent_is_nested_not_root_success(self) -> None:
        root_id, explorer_id, luna_id = "root-ancestry", "explorer-ancestry", "luna-ancestry"
        explorer_meta = {
            "timestamp": self.stamp(self.now),
            "type": "session_meta",
            "payload": {
                "id": explorer_id,
                "source": {
                    "subagent": {
                        "thread_spawn": {
                            "agent_role": "explorer",
                            "parent_thread_id": root_id,
                            "depth": 1,
                        }
                    }
                },
            },
        }
        self.write(
            self.root / "root.jsonl",
            [
                self.metadata(self.now, root_id),
                self.event(
                    self.now,
                    "event_msg",
                    {
                        "type": "sub_agent_activity",
                        "agent_thread_id": explorer_id,
                        "kind": "started",
                        "turn_id": "root-turn",
                    },
                ),
                self.event(
                    self.now + timedelta(seconds=3),
                    "event_msg",
                    {
                        "type": "task_complete",
                        "turn_id": "root-turn",
                        "last_agent_message": (
                            "Luna 验收：adopted=1 partial=0 rejected=0 failed=0"
                        ),
                    },
                ),
            ],
        )
        self.write(
            self.root / "explorer.jsonl",
            [
                explorer_meta,
                self.event(
                    self.now,
                    "event_msg",
                    {
                        "type": "sub_agent_activity",
                        "agent_thread_id": luna_id,
                        "kind": "started",
                        "turn_id": "explorer-turn",
                    },
                ),
                self.event(
                    self.now + timedelta(seconds=2),
                    "event_msg",
                    {"type": "task_complete", "turn_id": "explorer-turn", "last_agent_message": "explorer"},
                ),
            ],
        )
        self.write(
            self.root / "luna.jsonl",
            [
                self.metadata(self.now, luna_id, parent=explorer_id, depth=2),
                self.event(
                    self.now + timedelta(seconds=1),
                    "event_msg",
                    {"type": "task_complete", "turn_id": "luna-turn", "last_agent_message": "luna"},
                ),
            ],
        )

        audit = doctor.audit_sessions(self.root, 7)

        self.assertEqual(1, audit["root_completed"])
        self.assertEqual(1, audit["luna_nested"])
        self.assertEqual(1, audit["root_turns_with_luna"])
        self.assertEqual(0, audit["successful_root_turns_with_luna"])
        self.assertEqual(0, audit["root_turns_with_luna_outcome_report"])
        self.assertEqual(1, audit["luna_outcome_reports_invalid"])

    def test_luna_config_limit_states(self) -> None:
        config = self.root / "config.toml"

        config.write_text("[agents]\nmax_concurrent_threads_per_session = 5\n", encoding="utf-8")
        self.assertEqual("ok", doctor.check_luna_config(config)[0]["severity"])

        config.write_text("[agents]\n", encoding="utf-8")
        self.assertEqual("warning", doctor.check_luna_config(config)[0]["severity"])

        config.write_text("[agents]\nmax_concurrent_threads_per_session = 3\n", encoding="utf-8")
        self.assertEqual("warning", doctor.check_luna_config(config)[0]["severity"])

        config.write_text("[agents\nmax_concurrent_threads_per_session = 5\n", encoding="utf-8")
        self.assertEqual("error", doctor.check_luna_config(config)[0]["severity"])

        config.unlink()
        self.assertEqual("warning", doctor.check_luna_config(config)[0]["severity"])


class ReportTests(unittest.TestCase):
    def test_json_contract_and_exit_codes(self) -> None:
        report = doctor.make_report(
            checks=[
                doctor.check("warning", "sample-warning", "warning", section="skills"),
            ],
            worktrees=[],
            session_audit={
                "days": 7,
                "raw_completed": 5,
                "completed": 4,
                "duplicates_skipped": 1,
                "reports": 3,
            },
            docs_audit={"repositories": 0, "markdown_files": 0},
        )

        payload = json.loads(doctor.render_report(report, "json"))

        self.assertEqual(doctor.REPORT_VERSION, payload["version"])
        self.assertEqual({"errors": 0, "warnings": 1, "ok": 0}, payload["summary"])
        self.assertIn("skills", payload["section_summaries"])
        self.assertIn("worktrees", payload["section_summaries"])
        self.assertIn("sessions", payload["section_summaries"])
        self.assertNotIn("docs", payload["section_summaries"])
        self.assertEqual(6, payload["version"])
        self.assertEqual(0, doctor.report_exit_code(report, strict=False))
        self.assertEqual(1, doctor.report_exit_code(report, strict=True))

    def test_errors_fail_without_strict_mode(self) -> None:
        report = doctor.make_report(
            checks=[doctor.check("error", "sample-error", "error")],
            worktrees=[],
            session_audit={"days": 0, "completed": 0, "reports": 0},
        )
        self.assertEqual(1, doctor.report_exit_code(report, strict=False))

    def test_core_report_omits_full_scan_sections(self) -> None:
        report = doctor.make_report(
            checks=[doctor.check("ok", "core", "core passed")],
            worktrees=[],
            session_audit={"days": 0, "completed": 0, "reports": 0},
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
            session_audit={
                "days": 7,
                "raw_completed": 5,
                "completed": 4,
                "duplicates_skipped": 1,
                "reports": 2,
            },
        )

        rendered = doctor.render_report(report, "human")

        self.assertIn("[Skills]", rendered)
        self.assertIn("[Worktrees]", rendered)
        self.assertIn("[Sessions]", rendered)
        self.assertIn("duplicates_skipped=1", rendered)

    def test_sessions_render_all_luna_metrics_in_human_and_json(self) -> None:
        session_audit = doctor._audit_default(7)
        session_audit.update(
            {
                "root_completed": 2,
                "luna_started": 3,
                "luna_completed": 2,
                "luna_interrupted": 1,
                "luna_nested": 1,
                "luna_peak_concurrency": 2,
                "root_turns_with_luna": 2,
                "successful_root_turns_with_luna": 1,
            }
        )
        report = doctor.make_report(
            checks=[],
            worktrees=[],
            session_audit=session_audit,
            sections=["sessions"],
        )

        rendered = doctor.render_report(report, "human")
        payload = json.loads(doctor.render_report(report, "json"))

        for field, value in session_audit.items():
            self.assertEqual(value, payload["session_audit"][field])
            if field.startswith("luna_") or field.startswith("root_"):
                self.assertIn(f"{field}={value}", rendered)
        self.assertEqual(6, payload["version"])

    def test_docs_section_is_explicit_and_rendered(self) -> None:
        parser = doctor.build_parser()
        parsed = parser.parse_args(
            ["doctor", "--full", "--section", "docs", "--repo-root", "/tmp/repo"]
        )
        report = doctor.make_report(
            checks=[doctor.check("warning", "docs-sample", "docs", section="docs")],
            worktrees=[],
            session_audit={"days": 0, "completed": 0, "reports": 0},
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
            ["doctor", "--full", "--section", "worktrees", "--section", "sessions"]
        )
        self.assertEqual(["worktrees", "sessions"], parsed.section)

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
                exit_code = doctor.main(["doctor", "--session-days", "0"])
        finally:
            doctor._doctor_command = original

        self.assertEqual(2, exit_code)
        self.assertIn("ERROR: environment failed", stderr.getvalue())

    def test_session_audit_uses_event_timestamp_not_file_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sessions = Path(tmp)
            now = datetime.now().astimezone()
            events = [
                {
                    "timestamp": (now - timedelta(days=30)).isoformat(),
                    "type": "event_msg",
                    "payload": {
                        "type": "task_complete",
                        "last_agent_message": "规则沉淀：旧记录",
                    },
                },
                {
                    "timestamp": (now - timedelta(days=1)).isoformat(),
                    "type": "event_msg",
                    "payload": {
                        "type": "task_complete",
                        "last_agent_message": "规则沉淀：新记录",
                    },
                },
            ]
            session = sessions / "session.jsonl"
            session.write_text(
                "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
                encoding="utf-8",
            )

            audit = doctor.audit_sessions(sessions, 7)

            self.assertEqual(1, audit["completed"])
            self.assertEqual(1, audit["reports"])

    def test_session_audit_deduplicates_turns_across_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sessions = Path(tmp)
            now = datetime.now().astimezone()
            base = {
                "timestamp": (now - timedelta(hours=1)).isoformat(),
                "type": "event_msg",
                "payload": {
                    "type": "task_complete",
                    "turn_id": "turn-1",
                    "completed_at": (now - timedelta(hours=1)).isoformat(),
                    "last_agent_message": "完成",
                },
            }
            duplicate = json.loads(json.dumps(base, ensure_ascii=False))
            duplicate["payload"]["last_agent_message"] = "规则沉淀：已更新规则"
            (sessions / "a.jsonl").write_text(
                json.dumps(base, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            (sessions / "b.jsonl").write_text(
                json.dumps(duplicate, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            audit = doctor.audit_sessions(sessions, 7)

            self.assertEqual(2, audit["raw_completed"])
            self.assertEqual(1, audit["completed"])
            self.assertEqual(1, audit["duplicates_skipped"])
            self.assertEqual(1, audit["reports"])


if __name__ == "__main__":
    unittest.main()
