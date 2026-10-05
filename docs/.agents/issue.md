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

## RSI-003 发布前独立 Review 发现的契约漂移

**日期**：2026-10-04

**问题描述**：发布前独立 Review 发现 Archify workflow 曾将 Verify 直接连接到终态，重复 Finding eval 曾把行位置隐含为身份字段，Trigger eval 指南曾与官方 Runner 的 threshold 判定不一致。

**表因与根因**：视觉资产、行为评测和运行契约分别演进，缺少一次跨资产的发布前交叉核对。

**处理方式**：使用 Archify Lifecycle 表达 `Verify → Review/Re-review → 终态` 的语义路径，避免 Workflow 布局中的脆弱回环路由；将 Finding 断言改为规范化路径、失败模式/根因和触发场景；将 Trigger 指南同步为官方 Runner 的 `>= 0.5` / `< 0.5` 判定。

**后续防范**：发布前同时审查运行时主循环、评测断言和可视化资产；任何图表只能作为说明，不得改变运行契约的状态机语义。

**同类问题影响与注意事项**：视觉图、eval 和 runtime reference 出现同一概念时，只允许引用同一事实源；若图表为可读性做拓扑简化，必须保持所有关键状态转移可追踪。

## RSI-004 合并前外部 Review 发现的三项工具链漂移

**日期**：2026-10-05

**问题描述**：对 PR #1 的独立深度 Review 发现三项非阻塞缺陷：`evals/evals.json` 的字段名 `assertions` 与官方 skill-creator `references/schemas.md` 定义的 `expectations` 漂移（并附加非 schema 字段 `mode`）；README 两条安装命令硬编码 `--branch feat/review-once`，合并后分支删除即失效；[Review Contract](../../references/review-contract.md) 状态机首节点 `DISCOVER` 在 SKILL.md 主循环中无对应术语。

**表因与根因**：evals.json 官方仓库自身也存在命名漂移（其 SKILL.md 叙述称 assertions、schemas.md 示例用 expectations），且 `jq`/`quick_validate.py` 均不校验该文件，漂移被本地校验绿灯掩盖；安装命令在 PR 阶段编写，缺少“合并后时效”视角；状态机为图示性命名，未与运行时主循环的词汇表对齐。

**处理方式**：`assertions` 全部更名为 `expectations`，`mode` 在 [evals/README.md](../../evals/README.md) 明示为项目扩展；安装命令改为 `--branch main`（合并后即刻生效，第 35 行说明保持解释合并时序）；状态机首节点更名为 `BASELINE` 并标注对应主循环步骤 1–2。

**后续防范**：接入官方 skill-creator 工具链的字段以 `references/schemas.md` 为准，而不是官方文档叙述；任何硬编码分支名的面向用户命令都必须回答“该 Ref 在合并后是否仍存在”；跨文件共享的图示节点名必须能在运行时文档中检索到同词汇。

**同类问题影响与注意事项**：与 RSI-003 同属“多资产各自演进导致的漂移”，但此次漂移源部分来自上游（官方仓库内部不一致）；引用上游 schema 时应同时记录核验日期与具体文件，上游漂移不能自动豁免本仓库的一致性义务。

## RSI-005 评测文档覆盖声明与 Trigger 数据漂移

**日期**：2026-10-05

**问题描述**：外部 Review 发现 [evals/README.md](../../evals/README.md) 两处声明与数据不符：trigger-evals 实为“正负各半”（id 8、9 为连续两条负例），却被描述为“正负交替”；覆盖声明列出“发布 Release”，但当时 24 条 query 中无 Release 形态负例，导致 SKILL.md 触发边界中该项未被评测验证。

**表因与根因**：描述性声明沿用最初的数据组织方式，trigger 数据增删后未回查文档；覆盖清单按 SKILL.md 边界逐项抄写，但缺少“声明 ↔ 数据条目”的核对步骤。

**处理方式**：“正负交替”改为按数据陈述“共 25 条（12 正 / 13 负）”；新增 id 25 Release 形态负例（复用“变更/Review”词汇构造 collision case），并在 smoke 记录中标注该条晚于 2026-10-04 smoke 加入。

**后续防范**：评测文档中的数量、极性比例与覆盖清单必须与数据文件同批修改、同批校验；覆盖类声明逐条对应数据条目核对，不凭记忆抄写。

**同类问题影响与注意事项**：与 RSI-003、RSI-004 同属“多资产各自演进导致的漂移”，差异在于漂移源是本仓库内部的数据演进而非上游；凡“汇总类描述”（数量、比例、清单）都应视为可漂移资产，改动数据时同批回查。
