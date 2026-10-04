# Knowledge Map

本文件是 `review-once` Repo 的文档索引，避免使用分散的死文本引用。

## 入口

| 文档 | 内容 |
| --- | --- |
| [SKILL.md](../../SKILL.md) | Skill 触发边界、双 Mode 路由、主循环、收敛条件和交付格式 |
| [README.md](../../README.md) | 安装、调用、验证和评测入口 |
| [LICENSE](../../LICENSE) | MIT License |

## Review Contract

| 文档 | 内容 |
| --- | --- |
| [review-contract.md](../../references/review-contract.md) | Finding 判定、Fingerprint、状态机、证据和最终报告 |
| [conductor-mode.md](../../references/conductor-mode.md) | Conductor Diff/Comments/Checks 工作流 |
| [git-mode.md](../../references/git-mode.md) | Git fallback 的 base 探测、Diff 获取和验证 |

## Evals

| 文档 | 内容 |
| --- | --- |
| [evals/README.md](../../evals/README.md) | Output eval 与 Trigger eval 运行说明 |
| [evals/evals.json](../../evals/evals.json) | 双 Mode 和收敛行为评测 |
| [evals/trigger-evals.json](../../evals/trigger-evals.json) | Skill 触发准确率评测 |

## Research and Visual Evidence

| 文档 | 内容 |
| --- | --- |
| [Progressive Loop Research](../research/2026-10-04-review-once-progressive-loop-research.md) | Agent Skills、evaluator-optimizer、Conductor review gate 与真实案例调研 |
| [Workflow Candidate](../assets/review-once-workflow.candidate.json) | Archify workflow 的可编辑事实源 |
| [Workflow Diagram](../assets/review-once-workflow.html) | 通过 Archify validate、deliver、check、browser-check 的 standalone HTML |

## 外部规范

- [Agent Skills specification](https://agentskills.io/specification)
- [Claude Agent Skills best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Conductor review and merge](https://conductor.build/docs/guides/review-and-merge)
