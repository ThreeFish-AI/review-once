# review-once

Portable Agent Skill，用于在 Conductor 或普通 Git workspace 中执行有界的 Review-Fix loop：读取 Review 规则、审查当前 Diff、直接修复明确缺陷、运行验证，再重新 Review，直到收敛或明确阻塞。

## 适用场景

当用户说“反复 Review 当前 workspace 的变更，发现问题后直接修复，再 Review，直到没有明显问题”时使用：

```text
使用 review-once 反复执行 Review request.md 中的 Review，
把发现的明确缺陷挂载到 Chat 并直接修复，再 Review，直到收敛。
```

Skill 不负责自动 Commit、Push、创建或合并 PR，也不替用户完成 OAuth/SSO。

## 两种 Mode

| Mode | 反馈载体 | Diff 来源 | 适用环境 |
| --- | --- | --- | --- |
| Conductor | Checks 面板 + Chat | `GetWorkspaceDiff` | Conductor MCP 工具可用 |
| Git fallback | Chat | `git merge-base` + `git diff` | 普通 Claude Code、Codex 或无 Conductor 工具 |

Conductor Mode 的详细规则见 [references/conductor-mode.md](./references/conductor-mode.md)，Git fallback Mode 的详细规则见 [references/git-mode.md](./references/git-mode.md)。共同的 Finding 判定、终止条件和报告格式见 [references/review-contract.md](./references/review-contract.md)。

## 核心约束

- 只报告当前变更引入、离散、可证明且原作者会修复的缺陷。
- 修复后重新获取 Diff 和 Review 结果，不依赖陈旧结论。
- 最多 8 轮；重复 Finding、连续两轮无进展或工具/验证阻塞时安全停止。
- 测试失败必须分类处理；存在未解释失败时不得宣称 Review 已完成。
- 不默认向 GitHub 发布 Review；Conductor 评论使用 Checks 面板的 `DiffComment`。

## 安装

Repo 根目录即 Skill 根目录，不需要额外嵌套目录。当前实现位于 PR 工作分支 `feat/review-once`；合并后可从 `main` 获取。

Claude Code 用户级安装（目录已存在时先检查，不覆盖）：

```bash
git clone --branch feat/review-once https://github.com/ThreeFish-AI/review-once.git "$HOME/.claude/skills/review-once"
```

Codex 用户级安装：

```bash
git clone --branch feat/review-once https://github.com/ThreeFish-AI/review-once.git "$HOME/.agents/skills/review-once"
```

Claude Code 使用 `/review-once`，Codex 使用 `$review-once`，同时提供具体 Repo、base（如 `origin/feature/1.x.x`）与 Review request。发现不到 Skill 时重启当前 Agent 会话。安装路径及显式调用按 [Claude Code 文档](https://code.claude.com/docs/en/skills) 与 [OpenAI 文档](https://developers.openai.com/codex/skills/)；这里不引入插件、后台守护或新的全局权限。

Skill 是 instruction-only workflow，不是能绕过 Harness 权限的脚本。Plan Mode 下只做规划；无修复权限时停止并说明。无需 Conductor UI 自动点击、GitHub Token 配置或第三方 Agent 依赖。

## 校验与打包

仓库刻意不携带 `scripts/`。把 `CREATOR` 指向本机已安装的官方 [Skill Creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) 根目录（须包含 `scripts/quick_validate.py` 与 `scripts/package_skill.py`），从该目录以 module 运行：

```bash
SKILL_ROOT="/absolute/path/to/review-once"
CREATOR="/absolute/path/to/skill-creator"
cd "$CREATOR"
PYTHONPATH="$CREATOR" uv run --no-project --with pyyaml python "$CREATOR/scripts/quick_validate.py" "$SKILL_ROOT"
```

打包器会递归读取文件，并不保证排除 `.git/`、`.context/` 或 `.temp/`。先把运行时文件复制到仓库之外的干净 staging 目录，再打包（不是直接打包整个 clone）：

```bash
STAGE=$(mktemp -d)
mkdir -p "$STAGE/review-once"
cp "$SKILL_ROOT/SKILL.md" "$SKILL_ROOT/LICENSE" "$STAGE/review-once/"
cp -R "$SKILL_ROOT/agents" "$SKILL_ROOT/references" "$STAGE/review-once/"
PYTHONPATH="$CREATOR" uv run --no-project --with pyyaml python "$CREATOR/scripts/package_skill.py" "$STAGE/review-once" "$SKILL_ROOT/.temp/dist"
unzip -l "$SKILL_ROOT/.temp/dist/review-once.skill"
```

发布包只含 Skill 入口、UI 元数据、三份运行时 Reference 和 License；README、调研、评测及 `.git/` 永不进入包。若已安装官方 `skills-ref`，额外执行 `skills-ref validate "$SKILL_ROOT"`；未安装则如实记录“不适用”，不冒称 Portable 校验执行过。

## 评测

评测资产位于 [evals/README.md](./evals/README.md)：

- `evals/evals.json` 验证双 Mode、无 Finding、重复 Finding、无进展、测试失败等输出行为；
- `evals/trigger-evals.json` 验证触发准确率，并覆盖普通 Review、Conductor Review 和近邻 collision case。

## 许可证

本项目使用 [MIT License](./LICENSE)。

全量文档索引见 [Knowledge Map](./docs/.agents/knowledge-map.md)，运行契约仍以 [SKILL.md](./SKILL.md) 与直接引用的 References 为唯一入口。
