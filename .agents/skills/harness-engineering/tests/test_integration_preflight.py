from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "integration_preflight.py"


def run_git(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
    )


class IntegrationPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.remote = self.root / "origin.git"
        self.repo = self.root / "repo"
        self.publisher = self.root / "publisher"

        run_git("init", "--bare", "--initial-branch=main", str(self.remote), cwd=self.root)
        run_git("clone", str(self.remote), str(self.repo), cwd=self.root)
        self.configure(self.repo)
        (self.repo / "base.txt").write_text("base\n", encoding="utf-8")
        run_git("add", "base.txt", cwd=self.repo)
        run_git("commit", "-m", "base", cwd=self.repo)
        run_git("push", "-u", "origin", "main", cwd=self.repo)
        self.task_base = run_git("rev-parse", "HEAD", cwd=self.repo).stdout.strip()

        run_git("clone", str(self.remote), str(self.publisher), cwd=self.root)
        self.configure(self.publisher)

        run_git("switch", "-c", "codex/task", cwd=self.repo)
        (self.repo / "feature.txt").write_text("feature\n", encoding="utf-8")
        run_git("add", "feature.txt", cwd=self.repo)
        run_git("commit", "-m", "feature", cwd=self.repo)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    @staticmethod
    def configure(repo: Path) -> None:
        run_git("config", "user.name", "Harness Test", cwd=repo)
        run_git("config", "user.email", "harness@example.test", cwd=repo)

    def advance_remote_main(self) -> None:
        run_git("pull", "--ff-only", cwd=self.publisher)
        marker = self.publisher / "remote.txt"
        content = marker.read_text(encoding="utf-8") if marker.exists() else ""
        marker.write_text(content + "next\n", encoding="utf-8")
        run_git("add", "remote.txt", cwd=self.publisher)
        run_git("commit", "-m", "advance remote", cwd=self.publisher)
        run_git("push", "origin", "main", cwd=self.publisher)

    def run_preflight(
        self,
        *extra: str,
        task: str = "codex/task",
        task_base: str | None = None,
        repo: Path | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(repo or self.repo),
                "--task",
                task,
                "--task-base",
                task_base or self.task_base,
                "--target",
                "main",
                "--format",
                "json",
                *extra,
            ],
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout) if result.stdout.strip() else {}
        return result, payload

    def test_direct_ff_ignores_a_diverged_local_target_branch(self) -> None:
        base = run_git("rev-parse", "main", cwd=self.repo).stdout.strip()
        tree = run_git("rev-parse", f"{base}^{{tree}}", cwd=self.repo).stdout.strip()
        local_commit = subprocess.run(
            ["git", "commit-tree", tree, "-p", base, "-m", "local-only main"],
            cwd=self.repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        run_git("update-ref", "refs/heads/main", local_commit, cwd=self.repo)

        result, payload = self.run_preflight()

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("DIRECT_FF", payload["action"])
        self.assertEqual(self.task_base, payload["task_base_oid"])
        self.assertTrue(payload["baseline_checked"])
        self.assertEqual([], payload["extra_commits"])
        self.assertFalse(payload["task_shared"])
        self.assertNotEqual(local_commit, payload["target_oid"])

    def test_diverged_unshared_task_recommends_rebase(self) -> None:
        self.advance_remote_main()

        result, payload = self.run_preflight()

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("REBASE_THEN_FF", payload["action"])
        self.assertFalse(payload["task_shared"])

    def test_diverged_shared_task_requires_mr(self) -> None:
        run_git("push", "origin", "codex/task", cwd=self.repo)
        self.advance_remote_main()

        result, payload = self.run_preflight()

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("MR_REQUIRED", payload["action"])
        self.assertTrue(payload["task_shared"])

    def test_shared_task_requires_mr_even_when_target_can_fast_forward(self) -> None:
        run_git("push", "origin", "codex/task", cwd=self.repo)

        result, payload = self.run_preflight()

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("MR_REQUIRED", payload["action"])
        self.assertIn("shared", payload["reason"])

    def test_direct_target_branch_can_fast_forward_remote(self) -> None:
        run_git("branch", "-f", "main", "codex/task", cwd=self.repo)
        run_git("switch", "main", cwd=self.repo)

        result, payload = self.run_preflight(task="main")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("DIRECT_FF", payload["action"])
        self.assertFalse(payload["task_shared"])

    def test_diverged_direct_target_branch_stops(self) -> None:
        run_git("branch", "-f", "main", "codex/task", cwd=self.repo)
        run_git("switch", "main", cwd=self.repo)
        self.advance_remote_main()

        result, payload = self.run_preflight(task="main")

        self.assertEqual(2, result.returncode)
        self.assertEqual("STOP", payload["action"])
        self.assertIn("direct target branch has diverged", payload["reason"])

    def test_unpublished_commits_in_task_base_stop(self) -> None:
        run_git("switch", "main", cwd=self.repo)
        (self.repo / "historical.txt").write_text("historical\n", encoding="utf-8")
        run_git("add", "historical.txt", cwd=self.repo)
        run_git("commit", "-m", "historical unpublished", cwd=self.repo)
        unpublished = run_git("rev-parse", "HEAD", cwd=self.repo).stdout.strip()
        run_git("switch", "-c", "codex/with-history", cwd=self.repo)
        (self.repo / "current.txt").write_text("current\n", encoding="utf-8")
        run_git("add", "current.txt", cwd=self.repo)
        run_git("commit", "-m", "current task", cwd=self.repo)

        result, payload = self.run_preflight(
            task="codex/with-history",
            task_base=unpublished,
        )

        self.assertEqual(2, result.returncode)
        self.assertEqual("STOP", payload["action"])
        self.assertTrue(payload["baseline_checked"])
        self.assertEqual(
            [{"oid": unpublished, "subject": "historical unpublished"}],
            payload["extra_commits"],
        )

    def test_task_base_that_is_not_a_task_ancestor_stops(self) -> None:
        self.advance_remote_main()
        unrelated_base = run_git("rev-parse", "HEAD", cwd=self.publisher).stdout.strip()
        run_git("fetch", "origin", "main", cwd=self.repo)

        result, payload = self.run_preflight(task_base=unrelated_base)

        self.assertEqual(2, result.returncode)
        self.assertEqual("STOP", payload["action"])
        self.assertTrue(payload["baseline_checked"])
        self.assertIn("not an ancestor", payload["reason"])

    def test_task_already_on_target_is_reported(self) -> None:
        run_git("push", "origin", "codex/task:main", cwd=self.repo)

        result, payload = self.run_preflight()

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("ALREADY_INTEGRATED", payload["action"])

    def test_explicit_mr_policy_overrides_direct_ff(self) -> None:
        result, payload = self.run_preflight("--integration-mode", "mr-required")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("MR_REQUIRED", payload["action"])
        self.assertIn("project policy", payload["reason"])

    def test_dirty_task_worktree_stops(self) -> None:
        (self.repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")

        result, payload = self.run_preflight()

        self.assertEqual(2, result.returncode)
        self.assertEqual("STOP", payload["action"])
        self.assertIn("not clean", payload["reason"])

    def test_missing_task_ref_stops(self) -> None:
        result, payload = self.run_preflight(task="codex/missing")

        self.assertEqual(2, result.returncode)
        self.assertEqual("STOP", payload["action"])
        self.assertIn("local task branch", payload["reason"])

    def test_fetch_failure_stops(self) -> None:
        run_git("remote", "set-url", "origin", str(self.root / "missing.git"), cwd=self.repo)

        result, payload = self.run_preflight()

        self.assertEqual(2, result.returncode)
        self.assertEqual("STOP", payload["action"])
        self.assertIn("fetch", payload["reason"])

    def test_unrelated_task_and_target_histories_stop(self) -> None:
        unrelated_remote = self.root / "unrelated.git"
        unrelated_repo = self.root / "unrelated"
        run_git("init", "--bare", "--initial-branch=main", str(unrelated_remote), cwd=self.root)
        run_git("clone", str(unrelated_remote), str(unrelated_repo), cwd=self.root)
        self.configure(unrelated_repo)
        (unrelated_repo / "other.txt").write_text("other\n", encoding="utf-8")
        run_git("add", "other.txt", cwd=unrelated_repo)
        run_git("commit", "-m", "unrelated", cwd=unrelated_repo)
        run_git("push", "origin", "main", cwd=unrelated_repo)
        run_git("remote", "set-url", "origin", str(unrelated_remote), cwd=self.repo)

        result, payload = self.run_preflight()

        self.assertEqual(2, result.returncode)
        self.assertEqual("STOP", payload["action"])
        self.assertIn("unrelated histories", payload["reason"])

    def test_human_output_starts_with_stable_action(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(self.repo),
                "--task",
                "codex/task",
                "--task-base",
                self.task_base,
                "--target",
                "main",
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.stdout.startswith("Integration preflight: DIRECT_FF\n"))
        self.assertIn(f"Task base: {self.task_base}\n", result.stdout)
        self.assertIn("Baseline checked: true\n", result.stdout)

    def test_task_base_is_required(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(self.repo),
                "--task",
                "codex/task",
                "--target",
                "main",
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("--task-base", result.stderr)


if __name__ == "__main__":
    unittest.main()
