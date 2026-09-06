#!/usr/bin/env python3
"""Verify provenance records for bundled third-party skills."""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATT_CURRENT_SKILLS = {
    "codebase-design",
    "diagnosing-bugs",
    "domain-modeling",
    "tdd",
}
MATT_HISTORICAL_SKILLS = {
    "ask-matt",
    "grill-with-docs",
    "handoff",
}
MATT_LICENSE_BLOB = "bced086c85b98ba0b68860a295ce0e18b66938df"


def git_blob_sha(path: Path) -> str:
    content = path.read_bytes()
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content).hexdigest()


class ThirdPartyNoticesTests(unittest.TestCase):
    def test_frontend_design_retains_upstream_license_and_marks_derivative(self) -> None:
        skill_root = ROOT / ".agents" / "skills" / "frontend-design"

        notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        frontend_notice = notices.split("## frontend-design", 1)[1].split("## mattpocock/skills", 1)[0]
        self.assertIn("`SKILL.md` is a local derivative", frontend_notice)
        self.assertIn("original upstream Git blob ID is `decdff43d05908b4c1fc2cfd2d80fc5743440934`", frontend_notice)
        self.assertEqual(
            git_blob_sha(skill_root / "LICENSE.txt"),
            "f433b1a53f5b830a205fd2df78e2b34974656c7b",
        )

    def test_root_notice_covers_frontend_design(self) -> None:
        notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

        self.assertIn("not replaced by the repository-level Apache License 2.0", notices)
        self.assertIn("## frontend-design", notices)
        self.assertIn("https://github.com/anthropics/skills", notices)
        self.assertIn("2235be7c60b551f5de82ade908fd3816455afcda", notices)

    def test_matt_skills_record_upstream_and_local_derivatives(self) -> None:
        notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        matt_notice = notices.split("## mattpocock/skills", maxsplit=1)[1]
        listed_skills = set(
            re.findall(r"^- `\.agents/skills/([a-z0-9-]+)/`", matt_notice, re.MULTILINE)
        )

        self.assertEqual(listed_skills, MATT_CURRENT_SKILLS | MATT_HISTORICAL_SKILLS)
        self.assertIn("https://github.com/mattpocock/skills", matt_notice)
        self.assertIn("e9fcdf95b402d360f90f1db8d776d5dd450f9234", matt_notice)
        self.assertIn("7c24ba00f83f4074f56907699162b575e4308e2e", matt_notice)
        self.assertIn("ed27ff886d14ed556cb80dc74484358449578b5d", matt_notice)
        self.assertIn("local derivatives", matt_notice)

    def test_matt_skills_include_mit_terms_and_copyrights(self) -> None:
        repository_license = ROOT / "licenses" / "mattpocock-skills-MIT.txt"
        license_text = repository_license.read_text(encoding="utf-8")

        self.assertEqual(git_blob_sha(repository_license), MATT_LICENSE_BLOB)
        self.assertIn("MIT License", license_text)
        self.assertIn("Copyright (c) 2026 Matt Pocock", license_text)
        self.assertIn("Copyright (c) 2026 AnonymXXX (modifications)", license_text)
        self.assertIn("The above copyright notice and this permission notice", license_text)

        for skill in MATT_CURRENT_SKILLS:
            with self.subTest(skill=skill):
                skill_license = ROOT / ".agents" / "skills" / skill / "LICENSE.txt"
                self.assertEqual(git_blob_sha(skill_license), MATT_LICENSE_BLOB)
                self.assertEqual(skill_license.read_bytes(), repository_license.read_bytes())


if __name__ == "__main__":
    unittest.main()
