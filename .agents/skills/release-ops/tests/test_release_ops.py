from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "release_ops.py"
SPEC = importlib.util.spec_from_file_location("release_ops", MODULE_PATH)
release_ops = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = release_ops
SPEC.loader.exec_module(release_ops)


def run(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        args,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class PendingCommitTests(unittest.TestCase):
    def test_patch_equivalent_commit_is_not_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run("git", "init", "-b", "main", cwd=repo)
            run("git", "config", "user.name", "Release Test", cwd=repo)
            run("git", "config", "user.email", "release@example.test", cwd=repo)

            source = repo / "settings.txt"
            source.write_text("disabled\n", encoding="utf-8")
            run("git", "add", "settings.txt", cwd=repo)
            run("git", "commit", "-m", "base", cwd=repo)

            run("git", "switch", "-c", "target", cwd=repo)
            source.write_text("enabled\n", encoding="utf-8")
            run("git", "commit", "-am", "target wording", cwd=repo)

            run("git", "switch", "-c", "source", "main", cwd=repo)
            source.write_text("enabled\n", encoding="utf-8")
            run("git", "commit", "-am", "source wording", cwd=repo)

            pending = release_ops.plus_commits_from_git_cherry(repo, "target", "source")

            self.assertEqual(set(), pending)

    def test_same_subject_and_changed_lines_at_different_locations_stays_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run("git", "init", "-b", "main", cwd=repo)
            run("git", "config", "user.name", "Release Test", cwd=repo)
            run("git", "config", "user.email", "release@example.test", cwd=repo)

            source = repo / "settings.txt"
            source.write_text(
                "first section\ndisabled\nseparator\nsecond section\ndisabled\n",
                encoding="utf-8",
            )
            run("git", "add", "settings.txt", cwd=repo)
            run("git", "commit", "-m", "base", cwd=repo)

            run("git", "switch", "-c", "target", cwd=repo)
            source.write_text(
                "first section\nenabled\nseparator\nsecond section\ndisabled\n",
                encoding="utf-8",
            )
            run("git", "commit", "-am", "enable setting", cwd=repo)

            run("git", "switch", "-c", "source", "main", cwd=repo)
            source.write_text(
                "first section\ndisabled\nseparator\nsecond section\nenabled\n",
                encoding="utf-8",
            )
            run("git", "commit", "-am", "enable setting", cwd=repo)
            source_sha = run("git", "rev-parse", "HEAD", cwd=repo)

            pending = release_ops.plus_commits_from_git_cherry(repo, "target", "source")

            self.assertEqual({source_sha}, pending)


class ExplicitCommitBatchTests(unittest.TestCase):
    def test_explicit_commits_are_deduplicated_and_sorted_by_source_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run("git", "init", "-b", "main", cwd=repo)
            run("git", "config", "user.name", "Release Test", cwd=repo)
            run("git", "config", "user.email", "release@example.test", cwd=repo)

            source = repo / "settings.txt"
            source.write_text("base\n", encoding="utf-8")
            run("git", "add", "settings.txt", cwd=repo)
            run("git", "commit", "-m", "base", cwd=repo)

            source.write_text("base\nfirst\n", encoding="utf-8")
            run("git", "commit", "-am", "first feature", cwd=repo)
            first_sha = run("git", "rev-parse", "HEAD", cwd=repo)

            source.write_text("base\nfirst\nsecond\n", encoding="utf-8")
            run("git", "commit", "-am", "second feature", cwd=repo)
            second_sha = run("git", "rev-parse", "HEAD", cwd=repo)

            commits = release_ops.resolve_explicit_commits(
                repo,
                "main",
                [second_sha[:12], first_sha[:12], second_sha],
            )

            self.assertEqual([first_sha, second_sha], [commit.sha for commit in commits])


if __name__ == "__main__":
    unittest.main()
