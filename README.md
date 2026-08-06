# Codex Harness Engineering

**简体中文** | [English](README.en.md)

一套面向 Codex 的可版本化工程工作流：让 Codex 根据任务风险选择执行方式，调用合适的 Skill，
必要时隔离中高风险修改，完成必要验证，并只沉淀真正需要长期保留的项目知识。

你不需要先读完所有规则。推荐直接在 Codex 中打开或引用本仓库，让 Codex 解释它是否适合你的
使用方式，再决定是否接入。

## 推荐：直接询问 Codex

### 1. 了解这个仓库

在 Codex 中发送：

```text
请阅读 AnonymXXX/codex-harness-engineering，告诉我这个仓库是干什么的、解决了什么问题、
包含哪些核心组件、适合哪些用户，以及它的限制。请引用仓库中的具体文件作为依据，
不要只复述 README。
```

如果已经在 Codex 中打开了本仓库，可以把仓库名替换为“当前仓库”。

### 2. 分析接入后的收益和改变

让 Codex 结合你当前可访问的配置和使用情况进行个性化比较：

```text
请阅读这个仓库，并在我授权且当前环境可访问的范围内，检查我的 Codex 配置、已安装 Skills、
工作流和近期使用记录。分析如果接入这套 Harness Engineering，我的日常使用会发生什么变化。

请按“当前状态、接入后变化、实际收益、成本或风险、是否建议接入”输出，并引用仓库中的
具体文件作为依据。无法访问的记录请明确说明，不要猜测。
```

Codex 应重点比较以下方面：

| 方面 | 接入后可能发生的变化 |
| --- | --- |
| 风险控制 | 按 Fast、Standard、Heavy Lane 选择检查强度，中高风险任务在必要时使用独立 Git worktree。 |
| Skill 路由 | 根据代码设计、故障诊断、领域建模、TDD 等任务自动选择专业工作流。 |
| 验证 | 根据修改范围运行最小但可信的测试、lint、构建或 Doctor 检查。 |
| Git 与平台操作 | 使用可复用流程处理提交、GitHub 操作和发布任务，并保留明确的停止条件。 |
| 并行执行 | 子代理派发当前暂停（2026-08-06），主 Agent 直接完成工作；原 Worker 协议可从 Git 历史恢复。 |
| 知识沉淀 | 只有满足 Capture Gate 的长期规则和决策才进入项目文档，减少文档噪声。 |
| 恢复与升级 | 通过版本化配置、安装器、备份和健康检查在新机器上恢复工作流。 |

这些是工作流提供的能力，不代表每个任务都会使用全部机制。简单任务仍应保持轻量。

### 3. 让 Codex 安全接入

确认适合后，可以让 Codex 完成检查、安装和验证：

```text
请帮我接入 AnonymXXX/codex-harness-engineering。

先只读检查 ~/.codex、~/.agents/skills、当前 Git 状态和可能冲突，比较 core 与 daily，
并说明你推荐的 profile。如果我另外提供了私有 Overlay 路径和 Profile，只检查该本地来源，
不要尝试发现或克隆其他私有仓库。不要读取、复制或输出凭据、sessions、memory、cache
或其他敏感运行时数据。

修改前列出会影响的文件、备份策略、依赖和风险。在我确认前不要安装或改写文件。
确认后运行 harness_setup.py install，随后运行对应的 check、Skill index 检查和 Harness Doctor。
最后总结实际变更、备份位置、验证结果，以及是否需要新建 Codex 任务来加载规则和 Skills。
```

Codex 只能分析当前任务中你明确授权且本机可访问的内容。它无法访问的历史记录、远程数据或
其他设备配置，必须由你补充；不要根据不完整信息推断结论。

## 可选方案

- `core`：全局 Harness 规则、工作流，以及 Harness Engineering、代码设计、故障诊断、领域建模和 TDD
  五个核心 Skill。
- `daily`：包含 `core`，并增加 Git、GitHub、发布、Web、前端和微信小程序等常用 Skill。
- 私有 Overlay：可选的外部 Skill 仓库，由用户自行克隆并显式提供本地路径和 Profile。
  本仓库不会记录其地址、Skill 清单或凭据元数据。

完整公开 Skill 清单见 [docs/SKILLS.md](docs/SKILLS.md)。

## 手动安装

如果你希望不通过 Codex 操作，可在 macOS 上安装 Codex CLI、Git、Python 3 和 GitHub CLI，
然后运行：

```bash
gh repo clone AnonymXXX/codex-harness-engineering ~/.local/share/codex-harness-engineering
python3 ~/.local/share/codex-harness-engineering/scripts/harness_setup.py install --profile core
python3 ~/.local/share/codex-harness-engineering/scripts/harness_setup.py check --profile core
```

将 `core` 替换为 `daily` 可安装日常扩展。已经自行克隆私有 Overlay 时，显式传入其路径和
Profile：

```bash
python3 ~/.local/share/codex-harness-engineering/scripts/harness_setup.py install --profile daily --overlay-source /absolute/path/to/private-overlay --overlay-profile private
python3 ~/.local/share/codex-harness-engineering/scripts/harness_setup.py check --profile daily --overlay-source /absolute/path/to/private-overlay --overlay-profile private
```

安装器会备份冲突目标，但不会复制或覆盖机器相关的 `~/.codex/config.toml`、凭据、sessions、
memory 或 cache。安装完成后，新建一个 Codex 任务以加载全局规则、自定义 Agents 和 Skills。

前置条件、配置选择、更新、回滚和凭据处理详见
[docs/RECOVERY.md](docs/RECOVERY.md)。

## 目录结构

- `.codex/`：全局 Agent 规则、自定义 Agent 与 Harness 工作流文档。
- `.agents/skills/`：Harness Skill 系列及其可执行检查。
- `scripts/harness_setup.py`：安装、检查、文档生成和本机凭据引导入口。
- `profiles.json`：`core` 和 `daily` 的可执行清单。

本仓库按照相对于用户主目录的路径镜像文件。运行时状态、会话、记忆、凭据、缓存和无关 Skill
均被有意排除。

## 许可证

除 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 中标明的第三方组件外，本仓库采用
[Apache License 2.0](LICENSE) 许可。第一方作品的作者身份与适用范围记录在
[ORIGINAL_WORKS.md](ORIGINAL_WORKS.md) 中。第三方组件及其本地衍生内容继续独立遵循各自的许可条款。

## 赞助

如果本项目改善了你的 Codex 工作流，可以通过
[爱发电](https://afdian.com/a/codexharness)支持项目的持续维护。赞助完全自愿，不会改变仓库的
开源可用性，也不包含付费技术支持。
