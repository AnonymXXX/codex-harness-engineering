import json
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "worktree_bootstrap.py"


class WorktreeBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_bootstrap(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), str(self.root), *args],
            capture_output=True,
            text=True,
        )

    def test_rejects_a_non_git_directory(self) -> None:
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()

        result = subprocess.run(
            ["python3", str(SCRIPT), str(outside), "--dry-run"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("not a Git worktree", result.stderr)

    def test_project_hook_takes_priority_over_lockfiles(self) -> None:
        scripts = self.root / "scripts"
        scripts.mkdir()
        hook = scripts / "bootstrap-worktree.sh"
        hook.write_text(
            "#!/bin/sh\nprintf 'hook-ran\\n' > bootstrap-result.txt\n",
            encoding="utf-8",
        )
        hook.chmod(0o755)
        (self.root / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")

        result = self.run_bootstrap()

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            "hook-ran\n",
            (self.root / "bootstrap-result.txt").read_text(encoding="utf-8"),
        )
        self.assertIn("scripts/bootstrap-worktree.sh", result.stdout)

    def test_lockfiles_map_to_frozen_install_commands(self) -> None:
        cases = {
            "pnpm-lock.yaml": "pnpm install --frozen-lockfile",
            "package-lock.json": "npm ci",
            "yarn.lock": "yarn install --immutable",
            "bun.lock": "bun install --frozen-lockfile",
        }
        for lockfile, expected in cases.items():
            with self.subTest(lockfile=lockfile):
                for path in self.root.iterdir():
                    if path.name != ".git":
                        path.unlink()
                (self.root / lockfile).write_text("{}\n", encoding="utf-8")

                result = self.run_bootstrap("--dry-run")

                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn(expected, result.stdout)

    def test_package_manager_disambiguates_multiple_lockfiles(self) -> None:
        (self.root / "package.json").write_text(
            json.dumps({"packageManager": "pnpm@9.15.0"}) + "\n",
            encoding="utf-8",
        )
        (self.root / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
        (self.root / "package-lock.json").write_text("{}\n")

        result = self.run_bootstrap("--dry-run")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("pnpm install --frozen-lockfile", result.stdout)
        self.assertNotIn("npm ci", result.stdout)

    def test_ambiguous_lockfiles_fail_closed(self) -> None:
        (self.root / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
        (self.root / "package-lock.json").write_text("{}\n")

        result = self.run_bootstrap("--dry-run")

        self.assertEqual(2, result.returncode)
        self.assertIn("multiple package managers", result.stderr)

    def test_package_manager_requires_its_lockfile(self) -> None:
        (self.root / "package.json").write_text(
            json.dumps({"packageManager": "pnpm@9.15.0"}) + "\n",
            encoding="utf-8",
        )

        result = self.run_bootstrap("--dry-run")

        self.assertEqual(2, result.returncode)
        self.assertIn("requires pnpm-lock.yaml", result.stderr)

    def test_non_node_worktree_is_a_safe_no_op(self) -> None:
        (self.root / "README.md").write_text("# Sample\n", encoding="utf-8")

        result = self.run_bootstrap("--dry-run")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("no bootstrap action needed", result.stdout)


if __name__ == "__main__":
    unittest.main()
