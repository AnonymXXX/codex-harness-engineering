#!/usr/bin/env python3
"""Claude Code PreToolUse hook: check `git commit` messages against git-auto-commit rules.

Reads the hook JSON from stdin. When the Bash command runs `git commit` with a message
(`-m`, `-F <file>`, heredoc), it blocks with exit code 2 if:
- the subject is longer than 50 characters;
- the subject ends with a period;
- the subject strings several changes together (a semicolon, or two or more Chinese
  commas / enumeration commas) but there is no body;
- the second line is not blank when a body follows;
- the message contains a literal backslash-n instead of a real line break.

Commits whose message cannot be read (editor, -C/-c reuse, --no-edit, unreadable file)
are let through: the hook only blocks what it can see.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys

MAX_SUBJECT = 50
SEPARATORS = {"&&", "||", ";", "|", "&", "\n"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n(.*?)\n[ \t]*\2[ \t]*(?:\n|$)", re.S)


def split_segments(command: str) -> list[list[str]]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    lexer.commenters = ""
    segments: list[list[str]] = [[]]
    for token in lexer:
        if token in SEPARATORS or set(token) <= set(";&|"):
            segments.append([])
        else:
            segments[-1].append(token)
    return [s for s in segments if s]


def heredoc_body(text: str) -> str | None:
    match = HEREDOC.search(text)
    return match.group(3) if match else None


def inline_message(value: str) -> str:
    # Claude Code's own style: -m "$(cat <<'EOF' ... EOF)"
    if value.lstrip().startswith("$(") and "<<" in value:
        body = heredoc_body(value)
        if body is not None:
            return body
    return value


def parse_commit(args: list[str], workdir: str, command: str) -> list[str] | None:
    """Return message paragraphs, or None when the message is not given on the command line."""
    messages: list[str] = []
    i = 0
    while i < len(args):
        arg = args[i]
        nxt = args[i + 1] if i + 1 < len(args) else None
        if arg in ("--no-edit", "--fixup", "--squash") or arg.startswith(("--fixup=", "--squash=")):
            return None
        if arg in ("-C", "-c", "--reuse-message", "--reedit-message") or arg.startswith(
            ("--reuse-message=", "--reedit-message=")
        ):
            return None
        if arg == "--":
            break
        if arg.startswith("--message="):
            messages.append(inline_message(arg.split("=", 1)[1]))
        elif arg == "--message" and nxt is not None:
            messages.append(inline_message(nxt))
            i += 1
        elif arg.startswith("--file=") or (arg == "--file" and nxt is not None):
            if arg == "--file":
                path = nxt
                i += 1
            else:
                path = arg.split("=", 1)[1]
            text = read_file(path, workdir, command)
            if text is None:
                return None
            messages.append(text)
        elif arg.startswith("-") and not arg.startswith("--") and len(arg) > 1:
            # short option cluster such as -am, -m<msg>, -F<file>
            for pos, flag in enumerate(arg[1:], start=1):
                if flag in "mF":
                    rest = arg[pos + 1 :]
                    if not rest:
                        if nxt is None:
                            return None
                        rest = nxt
                        i += 1
                    if flag == "m":
                        messages.append(inline_message(rest))
                    else:
                        text = read_file(rest, workdir, command)
                        if text is None:
                            return None
                        messages.append(text)
                    break
                if flag in "Cc":
                    return None
                if flag in "tSu":
                    break  # takes an attached value; nothing else in the cluster
        i += 1
    return messages or None


def read_file(path: str, workdir: str, command: str) -> str | None:
    if path == "-":
        return heredoc_body(command)
    full = os.path.join(workdir, os.path.expanduser(path))
    try:
        with open(full, encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return None


def strip_comments(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.startswith("#"))


def problems(paragraphs: list[str]) -> list[str]:
    if any("\\n" in p for p in paragraphs):
        return ["提交信息里出现了字面的 \\n，不会变成换行。用 `git commit -F <文件>`，文件里写真正的换行。"]
    lines = strip_comments(paragraphs[0]).strip("\n").splitlines()
    if not lines:
        return []
    subject = lines[0].strip()
    rest = lines[1:]
    has_body = any(line.strip() for line in rest) or any(strip_comments(p).strip() for p in paragraphs[1:])
    found = []
    if len(subject) > MAX_SUBJECT:
        found.append(f"标题有 {len(subject)} 个字，超过 {MAX_SUBJECT} 字。只写对需求最重要的那一件事，其余放进正文。")
    if subject.endswith(("。", ".")):
        found.append("标题末尾不要加句号。")
    many = "；" in subject or ";" in subject or subject.count("，") + subject.count("、") >= 2
    if many and not has_body:
        found.append("标题用分号或多个逗号串了几件事，却没有正文。标题留最重要的一件，其余写成正文列表。")
    if rest and rest[0].strip():
        found.append("标题和正文之间要空一行。")
    return found


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    command = (data.get("tool_input") or {}).get("command") or ""
    if "commit" not in command or "git" not in command:
        return 0
    try:
        segments = split_segments(command)
    except ValueError:
        return 0
    workdir = data.get("cwd") or os.getcwd()
    found: list[str] = []
    for tokens in segments:
        if tokens and tokens[0] == "cd" and len(tokens) > 1:
            workdir = os.path.join(workdir, os.path.expanduser(tokens[1]))
            continue
        # skip env assignments, then expect git [global options] commit
        idx = 0
        while idx < len(tokens) and re.match(r"^\w+=", tokens[idx]):
            idx += 1
        if idx >= len(tokens) or os.path.basename(tokens[idx]) != "git":
            continue
        idx += 1
        gitdir = workdir
        while idx < len(tokens) and tokens[idx].startswith("-"):
            if tokens[idx] in ("-C", "-c") and idx + 1 < len(tokens):
                if tokens[idx] == "-C":
                    gitdir = os.path.join(workdir, os.path.expanduser(tokens[idx + 1]))
                idx += 2
            else:
                idx += 1
        if idx >= len(tokens) or tokens[idx] != "commit":
            continue
        paragraphs = parse_commit(tokens[idx + 1 :], gitdir, command)
        if paragraphs:
            found += problems(paragraphs)
    if not found:
        return 0
    lines = "\n".join(f"- {p}" for p in found)
    print(
        f"提交被拦下，信息不符合 git-auto-commit 的规则：\n{lines}\n"
        "先加载 git-auto-commit skill，按它写好提交信息再提交（有正文时用 `git commit -F <文件>`）。",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
