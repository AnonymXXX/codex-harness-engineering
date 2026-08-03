# Source Command

This file preserves the original local `~/.claude/commands/git-commit.md` command text that the `git-auto-commit` skill was derived from.

# Git 自动提交配置

## Commands

### /commit
> 智能分析代码变更。支持多文件逻辑拆分；针对单文件混合改动采取“主次描述”策略。

**Context:**
读取并分析当前 git status, git diff (staged and unstaged)。

**Role:**
你是一名资深技术专家，专注于维护清晰的 Git 提交历史。

**Task:**
1.  **全局分析**: 检查所有变动的文件。
2.  **逻辑分组与执行策略**:
    * **情况 A：不同模块，不同逻辑** (如 `User.ts` 改了登录, `Order.ts` 改了支付)
        * **行动**: 拆分提交。先 `git add User.ts` -> 提交；再 `git add Order.ts` -> 提交。
    * **情况 B：同一个文件，混合逻辑** (如 `User.ts` 同时包含 bug 修复和新字段)
        * **行动**: **不要尝试拆分文件**（避免 patch 风险）。将该文件作为一个整体提交。
        * **描述**: 找出改动量最大或最重要的逻辑作为 `<Subject>`。将次要改动详细列在 `<Body>` 中。
    * **情况 C：同模块/同功能的简单改动** (如多个小改动都在同一个业务模块)
        * **判断标准**:
            - 改动量小（单文件改动通常少于 50 行）
            - 逻辑简单（如加个参数、改个组件调用、变量改名）
            - 属于同一个业务模块或功能
        * **行动**: 可以合并为一个提交。
        * **描述**: 选取主要改动作为 `<Subject>`，其他改动列在 `<Body>` 中。
    * **情况 D：已有暂存 (Staged)**
        * **行动**: 直接对暂存区内容生成提交。
3.  **执行循环**: 依次处理，直到工作区干净。

**Rules:**
1.  **Type**: 保留英文 (`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`)。
2.  **Subject (标题)**:
    * **必须中文**。
    * 针对混合改动文件，选取**主要逻辑**命名。
    * 50 字符以内，无句号。
3.  **Body (正文)**:
    * **必须中文**。
    * 使用列表 (`- `) 分条描述。
    * 如果存在正文，最终提交信息必须是：标题一行，空一行，正文列表。
4.  **Command Construction**:
    * 有正文时默认使用临时消息文件，再执行 `git commit -F <message-file>`。
    * 在这个工作流里，**不要**把标题和正文写进同一个 `-m` 参数。Git 在手动补出空行时可以正确存储，但这种写法很容易漏掉分隔空行，导致标题和正文连在一起。
    * **不要**给每条正文单独传一个 `-m`，否则 Git 会在条目之间插入空段落。
    * 可接受的结构是：消息文件首行写标题，第二行留空，第三行开始写 `- ` 列表正文。

**Execution Strategy:**
* **不要**等待确认，直接执行。
* **不要**使用 `git add .`，除非所有文件都属于同一个逻辑。
* **不要**尝试使用 `git add -p`。
* 如果文件未暂存，根据上述逻辑分组，使用 `git add <filepath>` 逐个/逐组提交。
* 有正文时，提交后执行 `git log --format=%B -1 HEAD` 复核第二行是否为空行；如果不是，立即使用正确的消息文件执行 `git commit --amend -F <message-file>` 修正。

**Output Control:**
* **不要**输出 Markdown 代码块。
* 直接展示执行结果。
* 每完成一个提交，输出： `✅ [模块/文件名] 提交成功: <Subject>`
* 全部完成后，输出： `🎉 所有变更处理完毕`

## Guidelines

* **Code Style**: 遵循项目风格。
* **Language**: 提交信息全中文。
