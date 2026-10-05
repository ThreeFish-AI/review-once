# `review-once` 双 Mode 有界 Review-Fix 设计调研

> 核验日期：2026-10-04（Asia/Shanghai）。本文只沉淀规范核验、设计依据与真实案例；运行时契约仍以 [`SKILL.md`](../../SKILL.md) 和 [`Review Contract`](../../references/review-contract.md) 为唯一事实源，本文不复制主循环规则。

## 结论先行

`review-once` 适合采用一个 Skill、两个运行 Mode、一个共享 Review Contract 的结构：Conductor Mode 负责 Diff/Checks/Comments 载体，Git fallback Mode 负责在无 Conductor 工具时提供等价证据链；两者在 Review 后汇入同一条 Chat → Fix → Verify → Re-review 主路径。该结构同时满足 Agent Skills 的 progressive disclosure、Anthropic 的 evaluator-optimizer 反馈闭环，以及 Conductor 对 Diff、Checks、未解决评论和失败检查的合并前门禁要求。[1]–[4]

## 1. Primary sources 核验

### 1.1 Progressive disclosure：成立，但不是复制两套流程

Agent Skills specification 定义了最小目录单元：`SKILL.md` 必需，`scripts/`、`references/`、`assets/` 可选；规范强调 Skill 的元数据、说明正文和按需资源是分层装载的基础。Anthropic Agent Skills best practices 进一步将 `SKILL.md` 定位为 overview/router，建议正文控制在约 500 行以内、引用文件从入口直接指向，避免深层引用导致只读到不完整上下文。[1], [2]

对本 Skill 的落地含义是：

- `SKILL.md` 只保留触发边界、Mode 路由、不变量和指向性链接；
- `references/conductor-mode.md`、`references/git-mode.md` 保留 Mode-specific 取证与工具纪律；
- `references/review-contract.md` 保持 Finding、Fingerprint、状态和停止条件的唯一契约；
- 本调研文档只解释为什么这样设计，不另建可执行规则副本。

这不是把同一循环复制成两个 Skill，而是把“变动维度”限定在取证载体，把“稳定维度”收敛到共享契约，降低跨宿主漂移。

### 1.2 Evaluator-optimizer：适合 Review-Fix，但必须有可判定反馈

Anthropic 对 evaluator-optimizer workflow 的定义是：一个 LLM 生成结果，另一个 evaluator 提供反馈，系统在循环中迭代；它适用于存在清晰评价标准、且人工反馈能带来可观测改进的任务。[3] `review-once` 的自然映射是：Review 生成 Finding，Chat 暴露证据与影响，Fix 修改当前变更，Verify 提供测试/检查结果，Re-review 判断 Finding 是否仍存在。

关键限制是 evaluator 不能只输出“看起来更好”：

- Finding 必须来自当前 Diff，并能指向影响场景和证据；
- Verify 失败必须分类，不能被循环吞掉；
- Re-review 必须重新取证，不能复用上一轮陈旧 Diff 或评论；
- 无 Finding 才是正常收敛，无法安全修复则是阻塞，不是继续空转。

因此 evaluator 的输出不是“更多问题”，而是可执行、可复核的最小 Finding 集合。

### 1.3 Bounded loop：最大轮次是控制面，不是质量捷径

Anthropic 的 agent workflow 讨论明确把最大迭代次数列为常见 stopping condition，用于保持控制；同一材料也指出，反馈循环适合有清晰成功标准、能通过环境结果评估进展的任务。[3] `review-once` 的默认 8 轮、重复 Finding、连续无进展、工具/验证阻塞等停止条件已写入 [`SKILL.md`](../../SKILL.md) 与 [`Review Contract`](../../references/review-contract.md)，本调研不重新定义它们。

设计判断：

1. “最多 8 轮”防止评审代理因微小偏好持续扩大范围；
2. “重复 Finding / 无进展”防止同一证据被改写成伪进步；
3. “阻塞”保留真实不确定性，避免用“已收敛”掩盖环境缺失或验证失败；
4. 每轮重新获取 Diff、评论和验证结果，保证停止判定基于新证据。

### 1.4 Conductor review-and-merge：Review-Fix 不等于 Merge

Conductor 官方流程要求先在 Diff Viewer 检查文件变更，再使用 Review 动作；Checks 聚合 Git 状态、PR metadata、CI、部署、GitHub/Review comments 和 Todos；未解决评论、失败检查和开放 Todo 在有意清理前都应视为 blocker。只有批准、检查通过、评论处理完、Todo 完成后才进入 Merge，随后 Archive workspace。[4]

因此 `review-once` 只负责工作区内的 Review-Fix loop，不自动 Commit、Push、Create PR 或 Merge；这与现有 Skill 的提交边界一致，也避免把“局部修复完成”错误升级成“PR 可合并”。

## 2. 真实案例：`to-video` PR #33

### 2.1 事实基线

- PR：[`ThreeFish-AI/to-video#33`](https://github.com/ThreeFish-AI/to-video/pull/33)
- 标题：`feat(rsi): IndexTTS 终声「人为触发原则」硬闸 --final-voice（RSI-040）`
- 合并时间：2026-10-04（具体时间以 GitHub PR metadata 为准）
- 合并 Commit：`2bf9656f0e01a4aa5e4290718e27c7fc85937741`
- 变更规模：21 个文件，475 insertions，68 deletions
- 结果：三轮 Review，共 12 个缺陷全部修复，第三轮独立盲扫后收敛。

以上事实来自 PR body、GitHub PR metadata，以及合并 Commit 中的 `docs/.agents/issue.md` 台账；未使用第三方镜像。[5]

### 2.2 三轮缺陷与闭环价值

| Round | Review 视角 | Findings | 关键缺陷 | 对 `review-once` 的启示 |
| --- | --- | ---: | --- | --- |
| 1 | 代码 / 文档 / 测试三镜头 | 7 | 5 处可执行文案漏 `--final-voice`、eval 示例误导、`all` 测试空转绿灯，另修一处旧编号笔误 | Review 必须覆盖实现、文档、测试三类证据；文案中的可执行命令也属于行为契约 |
| 2 | 修复核验 + Staff 终审 | 4 | `rc==2` 短路误泛化、07/10 跨会话授权口径矛盾、`cmd_all` 报错处方误导、台账漏登/计数失实 | Verify 不是只跑测试；需复核错误语义、跨文档一致性和事实台账 |
| 3 | 修复核验 + 独立盲扫 | 1 | 主闸 docstring 残留了已回撤的失实短路说明 | Re-review 能发现“代码已改、说明未改”的残余；独立视角是有效的 evaluator，不应省略 |

### 2.3 案例抽象出的工程约束

PR #33 最有价值的不是“增加一个 flag”，而是将一次昂贵操作的授权从持久状态中分离出来：`.engine` 只回答变化检测，不能证明本次操作获得了用户授权；因此 `--final-voice` 被定义为命令行级、瞬时、可审计的意图声明。该决策又要求 `pipeline.py` 不结构性透传、`tts_resume.py` 在冷重启前预检，并同步更新文档、模板、Schema 和测试。[5]

这对应 `review-once` 的三个可复用模式：

- **根因优先**：不是给旧护栏再加一个例外，而是纠正“变化检测 = 授权门”的职责混淆；
- **全链路一致性**：实现、调用包装器、恢复路径、文档、测试和 eval 必须一起复核；
- **保留残余面**：`tts_sample`、HTTP 直连和旧副本未纳入机器闸，台账如实登记，而不是把边界外问题伪装成闭环完成。

## 3. 对当前 Skill 的设计裁定

| 设计问题 | 裁定 | 依据 |
| --- | --- | --- |
| 是否拆成两个 Skill | 否；保留一个 `review-once`，两个 Mode 只拆 references | progressive disclosure；共享 Review Contract |
| Review 输出是否直接驱动 Fix | 是，但仅限当前 Diff 中明确、可证明且安全的 Finding | evaluator-optimizer 的可判定反馈要求 |
| 是否持续到“没有任何可能问题” | 否；以无明确 Finding、阻塞或有界停止为终态 | bounded loop 与 Conductor blocker 语义 |
| 是否把 Conductor Review 直接等同于 Merge readiness | 否；Merge 另受 Checks、评论、Todo、批准和 CI 约束 | Conductor review-and-merge |
| 是否把案例台账规则复制进本 Skill | 否；只引用事实源与来源 | Single Source of Truth |

## 4. 引用与可复核性

本文引用均为官方 primary source 或变更项目的第一方 PR/Commit；没有使用第三方镜像。网页与 API 于 2026-10-04 在本机通过 `curl` / `gh api` 核验可访问；PR #33 事实同时由本地 `to-video` Git object 与 GitHub API 交叉核对。

## 参考文献（IEEE）

[1] Agent Skills, “Specification,” *Agent Skills Documentation*, 2026. [Online]. Available: https://agentskills.io/specification (accessed Oct. 4, 2026).

[2] Anthropic, “Agent Skills: Best practices,” *Claude Documentation*, n.d. [Online]. Available: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices (accessed Oct. 4, 2026).

[3] Anthropic, “Building effective agents,” *Anthropic Engineering*, Dec. 19, 2024. [Online]. Available: https://www.anthropic.com/engineering/building-effective-agents (accessed Oct. 4, 2026).

[4] Conductor, “Review and merge a workspace,” *Conductor Documentation*, n.d. [Online]. Available: https://conductor.build/docs/guides/review-and-merge (accessed Oct. 4, 2026).

[5] ThreeFish-AI, “feat(rsi): IndexTTS 终声「人为触发原则」硬闸 --final-voice（RSI-040）, PR #33,” *GitHub Pull Request*, Oct. 4, 2026. [Online]. Available: https://github.com/ThreeFish-AI/to-video/pull/33 (accessed Oct. 4, 2026).
