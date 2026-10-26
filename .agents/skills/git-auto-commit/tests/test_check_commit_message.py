#!/usr/bin/env python3
"""Run the commit-message hook against sample Bash commands."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_commit_message.py"
LONG = "调整首页快捷入口为写日记记便便记花费记一笔，去掉文本框缩放角，记录表单支持选择或输入药品疫苗剂量并修复键盘遮挡备注输入框"


def run(command: str, cwd: str = "/tmp") -> subprocess.CompletedProcess[str]:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd})
    return subprocess.run([sys.executable, str(SCRIPT)], input=payload, capture_output=True, text=True)


class CheckCommitMessageTests(unittest.TestCase):
    def assertBlocked(self, command: str, cwd: str = "/tmp", reason: str = "") -> None:
        result = run(command, cwd)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(reason, result.stderr)

    def assertAllowed(self, command: str, cwd: str = "/tmp") -> None:
        result = run(command, cwd)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_ignores_other_commands(self) -> None:
        self.assertAllowed("git status && ls")
        self.assertAllowed("echo 'git commit -m x'")

    def test_short_subject_passes(self) -> None:
        self.assertAllowed('git commit -m "修复首页礼炮位置"')
        self.assertAllowed("cd /tmp && git add -A && git commit -am 'chore: release v1.0.12'")

    def test_long_subject_blocked(self) -> None:
        self.assertBlocked(f'git commit -m "{LONG}"', reason="超过 50 字")
        self.assertBlocked(f"git -C /tmp commit --message='{LONG}'", reason="超过 50 字")

    def test_many_items_without_body_blocked(self) -> None:
        self.assertBlocked('git commit -m "首页改快捷入口；去掉缩放角"', reason="没有正文")
        self.assertBlocked('git commit -m "改快捷入口，去掉缩放角，调大照片"', reason="没有正文")

    def test_many_items_with_body_passes(self) -> None:
        self.assertAllowed('git commit -m "改快捷入口，去掉缩放角，调大照片" -m "- 细节见正文"')

    def test_period_and_literal_newline_blocked(self) -> None:
        self.assertBlocked('git commit -m "修复礼炮位置。"', reason="句号")
        self.assertBlocked('git commit -m "修复礼炮位置\\n- 细节"', reason="\\n")

    def test_message_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "good.txt").write_text("修复礼炮位置\n\n- 改为相对列表定位\n- 撤销改成乐观更新\n", encoding="utf-8")
            Path(tmp, "nogap.txt").write_text("修复礼炮位置\n- 改为相对列表定位\n", encoding="utf-8")
            Path(tmp, "long.txt").write_text(LONG + "\n", encoding="utf-8")
            self.assertAllowed("git commit -F good.txt", cwd=tmp)
            self.assertAllowed(f"cd {tmp} && git commit --file=good.txt")
            self.assertBlocked("git commit -F nogap.txt", cwd=tmp, reason="空一行")
            self.assertBlocked("git commit --file long.txt", cwd=tmp, reason="超过 50 字")
            self.assertAllowed("git commit -F missing.txt", cwd=tmp)

    def test_heredoc_messages(self) -> None:
        good = "git commit -m \"$(cat <<'EOF'\n修复礼炮位置\n\n- 改为相对列表定位\nEOF\n)\""
        bad = f"git commit -m \"$(cat <<'EOF'\n{LONG}\nEOF\n)\""
        stdin = f"git commit -F - <<'EOF'\n{LONG}\nEOF"
        self.assertAllowed(good)
        self.assertBlocked(bad, reason="超过 50 字")
        self.assertBlocked(stdin, reason="超过 50 字")

    def test_unreadable_messages_pass(self) -> None:
        self.assertAllowed("git commit")
        self.assertAllowed("git commit --amend --no-edit")
        self.assertAllowed("git commit -C HEAD~1")


if __name__ == "__main__":
    unittest.main()
