#!/usr/bin/env python3
"""Verify license records for the repository's confirmed original Skills."""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_SKILLS = {
    "develop-uniapp-miniapp",
    "git-auto-commit",
    "github-cli-ops",
    "harness-engineering",
    "release-ops",
    "wechat-miniprogram-ci-upload",
}
NON_ORIGINAL_SKILLS = {
    "codebase-design",
    "diagnosing-bugs",
    "domain-modeling",
    "tdd",
}
APACHE_LICENSE_BLOB = "f433b1a53f5b830a205fd2df78e2b34974656c7b"


def git_blob_sha(path: Path) -> str:
    content = path.read_bytes()
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content).hexdigest()


class OriginalSkillLicenseTests(unittest.TestCase):
    def test_repository_has_the_apache_license_terms(self) -> None:
        self.assertEqual(git_blob_sha(ROOT / "LICENSE"), APACHE_LICENSE_BLOB)

    def test_original_works_has_exact_confirmed_skill_allowlist(self) -> None:
        original_works = (ROOT / "ORIGINAL_WORKS.md").read_text(encoding="utf-8")
        listed_skills = set(
            re.findall(r"^- `\.agents/skills/([a-z0-9-]+)/`$", original_works, re.MULTILINE)
        )

        self.assertEqual(listed_skills, ORIGINAL_SKILLS)
        for skill in NON_ORIGINAL_SKILLS:
            self.assertNotIn(f".agents/skills/{skill}/", original_works)

    def test_original_works_records_author_source_and_license(self) -> None:
        original_works = (ROOT / "ORIGINAL_WORKS.md").read_text(encoding="utf-8")

        self.assertIn("Copyright 2026 AnonymXXX", original_works)
        self.assertIn("authored by **AnonymXXX**", original_works)
        self.assertIn(
            "https://github.com/AnonymXXX/codex-harness-engineering",
            original_works,
        )
        self.assertIn("Apache License 2.0", original_works)
        self.assertIn("git-commit-command.md", original_works)
        self.assertIn("Harness rules, agents", original_works)
        self.assertIn("THIRD_PARTY_NOTICES.md", original_works)
        self.assertIn("does not replace those terms", original_works)

    def test_each_original_skill_has_the_apache_license_terms(self) -> None:
        for skill in ORIGINAL_SKILLS:
            with self.subTest(skill=skill):
                license_path = ROOT / ".agents" / "skills" / skill / "LICENSE.txt"
                self.assertTrue(license_path.is_file())
                self.assertEqual(git_blob_sha(license_path), APACHE_LICENSE_BLOB)

    def test_readme_links_license_boundaries(self) -> None:
        readme_zh = (ROOT / "README.md").read_text(encoding="utf-8")
        readme_en = (ROOT / "README.en.md").read_text(encoding="utf-8")

        for readme in (readme_zh, readme_en):
            self.assertIn("[ORIGINAL_WORKS.md](ORIGINAL_WORKS.md)", readme)
            self.assertIn("[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)", readme)
            self.assertIn("[Apache License 2.0](LICENSE)", readme)

        self.assertIn("第三方组件及其本地衍生内容继续独立遵循各自的许可条款", readme_zh)
        self.assertIn("Third-party license terms continue to apply independently", readme_en)


if __name__ == "__main__":
    unittest.main()
