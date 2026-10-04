# Issue 台账

## RSI-001 `review-once` 缺少可收敛的 Review-Fix 闭环

**日期**：2026-10-04

**问题描述**：用户需要反复执行“Review 当前 workspace → 发现缺陷 → 直接修复 → 再 Review”，不再依赖人工反复点击 Review 和 Fix；该过程同时需要适配 Conductor 和无 Conductor 的普通 Git workspace。

**表因与根因**：一次性 Review 结果与工作区修复之间没有统一状态机；Conductor 的 Diff、Comments 和 Checks 能力也不能直接假设存在于所有 Runtime。若没有明确的 Finding 判定、重新取证和停止条件，循环容易变成重复评论、无效重构或无限运行。

**处理方式**：新增 `review-once` Portable Skill，使用一个 Skill 加两个 Mode 路由；以 [Review Contract](../../references/review-contract.md) 约束 Finding 的证据和唯一性，以 [Conductor Mode](../../references/conductor-mode.md) 与 [Git Mode](../../references/git-mode.md) 分离工具边界；默认最多 8 轮，并在重复 Finding、连续无进展、工具/验证阻塞或产品决策不足时停止。

**后续防范**：后续新增自动化脚本前，先证明操作顺序、权限边界或校验逻辑确实需要确定性执行；所有新增 Mode 必须补充 output eval、trigger eval 和失败路径；不得将用户凭证、Review 私有内容或平台内部状态写入仓库。

**同类问题影响与注意事项**：凡是“自动循环直到通过”的 Agent workflow，都必须同时定义成功状态、阻塞状态、有界停止和证据报告；“没有新发现”与“工具不可用”不是同一种结果，不能混写为已通过。

## RSI-002 Trigger eval Runner 的正例证据不足

**日期**：2026-10-04

**问题描述**：官方 `run_eval.py` 在本机对 24 条 Trigger query 执行单次 smoke 时得到 12/24；12 条负例通过，12 条正例均未记录触发。该结果不能直接证明 Description 不触发，因为单 query trace 已确认临时 Skill 命令被加载，但 Runner 未观察到 `Skill` tool invocation。

**表因与根因**：Trigger Runner 的判定依赖模型在短超时窗口内显式调用临时 Skill/Read 工具；当前 Runtime 使用的模型与命令发现路径会先读取 `Review request.md`，不一定调用临时命令名，导致自然语言正例出现 false negative。

**处理方式**：保留官方数组格式的 24 条 query、负例边界和本机 smoke 输出；不把 12/24 宣称为通过。以 `quick_validate.py`、`jq`、单 query trace 和后续真实宿主验证作为补充证据，并在评测文档中明确该限制。

**后续防范**：在支持原生 Skill loader 的 Runtime 中重复运行 Trigger eval；同时保留显式 `/review-once` / `$review-once` 调用样例，区分“Description 触发能力”和“Runner 是否观察到工具调用”。

**同类问题影响与注意事项**：任何依赖模型主动调用工具的 eval 都必须记录 Runtime、模型、超时、命令发现方式和工具事件；没有事件证据时只能标记“未验证”，不能把 false negative 当作 Skill 逻辑缺陷。
