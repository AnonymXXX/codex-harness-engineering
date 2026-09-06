# Commit Message Examples

Use this reference when a commit needs a body. [Git Auto Commit](../SKILL.md) owns current scope, grouping, and execution rules. The original `/commit` command is preserved in Git history; it is not a second active instruction source.

## Message File

Write a UTF-8 message file with actual newlines, one blank separator after the Chinese subject, and no blank lines between body bullets:

```text
fix: 修复登录过期后的页面跳转

- 统一处理会话失效后的返回位置
- 补充会话过期的行为回归测试
```

Use `git commit -F <message-file>`, then inspect `git log --format=%B -1 HEAD`. Correct malformed spacing only by safely amending the unshared current-task commit. Never amend shared history automatically.

A subject-only message is sufficient when it fully describes one clear change. For an authorized mixed file, describe its dominant behavior in the subject and secondary changes in the body; unrelated or unauthorized changes in that file remain outside the commit scope.
