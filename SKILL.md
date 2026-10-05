---
name: review-once
description: >-
  Run a bounded, evidence-driven Review-Fix loop for an existing workspace change.
  Trigger when the user asks to repeatedly review the current Diff or workspace,
  read Review request.md, fix actionable Findings directly, report them in Chat,
  and review again until no clear defects remain. This includes requests to avoid
  manual Review/Fix clicks, use Conductor Checks and DiffComments, or use Git
  merge-base and git diff as a fallback. Prefer Conductor Diff/Comments tools
  when available; otherwise use Git diff and repository-local checks. Do not
  trigger for ordinary code explanations, one-pass reviews, test-only requests,
  security audits without a Review-Fix loop, or release/merge automation.
license: MIT
metadata:
  short-description: Convergent Review-Fix loops for workspace changes
---

# review-once

一次授权，执行多轮 Review；不是只审一次。将人工驱动的 Review/Fix 流程收敛为有证据、有边界、可停止的循环，默认不要求用户反复点击 Review/Fix。只修复当前变更中明确、可证明且原作者会接受的缺陷。

## 触发边界

当用户要求“反复 Review、发现问题后直接修复、再 Review，直到没有明显问题”时使用本 Skill。典型入口包括：

- 用户已经授权自动反复执行 `Please review the changes in this workspace @Review request.md`；
- “自动反复审查当前 Diff 并修复 Findings”；
- “不要让我手动点击 Review 和 Fix，持续到收敛”。

以下请求不触发本 Skill：一次性 Review、解释已有代码、只运行测试、创建或合并 PR、发布 Release，以及没有待审查变更的普通开发任务。

## 不变量

1. **规则优先级**：首先服从当前 Harness 的 System/Developer 指令、权限和执行模式；在其允许范围内，用户明确要求与适用 Repo 规则优先于本 Skill 默认规则。指定的 `Review request.md` 提供具体 Review 标准，不可覆盖更高层限制；未提供时使用 [Review Contract](references/review-contract.md)。明确指定却无法读取时停止并报告，不静默替换。
2. **证据优先**：Finding 必须指向当前变更引入的离散行为、影响场景和证据；不因“看起来不优雅”而制造 Finding。
3. **最小根因修复**：修复应局部、可验证，不顺手重构无关模块，不改变用户未授权的产品决策。
4. **每轮重新取证**：修复后重新获取 Diff、评论和测试结果；禁止使用上一轮的陈旧结论宣称收敛。
5. **安全边界**：不自动完成 OAuth/SSO，不读取或索取密码、Cookie、Token，不执行破坏性 Git 操作，不默认向 GitHub 发布 Review。
6. **提交边界**：本 Skill 默认只修改工作区，不自动 Commit、Push、创建或合并 PR；只有用户另行明确要求时才进入 Git 发布流程。

## 执行路由

先确认目标 Repo/worktree 与 Conductor 绑定的 workspace 一致，再判断当前 Runtime 是否提供 Conductor 的 Diff/Comments 工具：

- **Conductor Mode**：工具可用时，读取 [Conductor Mode](references/conductor-mode.md)，以 Checks 面板为 Review 反馈载体。
- **Git fallback Mode**：工具不可用时，读取 [Git Mode](references/git-mode.md)，以 merge-base Diff、仓库检查和 Chat 记录完成同等闭环。

如果 Conductor 工具在执行中失效，但 Git 信息完整可取，可降级到 Git fallback；必须在 Chat 中说明降级。两种 Mode 都遵循 [Review Contract](references/review-contract.md)。

## 主循环

每轮严格按以下顺序执行：

1. **加载上下文**：定位用户指定的 `Review request.md`；读取适用的 Repo 规则、当前 Diff、已有 Review 评论和相关测试入口。
2. **建立基线**：记录本轮基线 Ref、工作区未提交 Diff、待审查文件和当前轮次。无法确认正确基线时停止，不盲审错误范围。
3. **Review**：按 Review Contract 筛选 Findings；一次 Finding 只代表一个离散问题，评论范围尽量保持在能理解问题的最短行区间。
4. **Chat 报告**：先列出 Finding 的严重性、位置、影响场景和证据。没有 Finding 时明确报告“本轮无明确值得修复的缺陷”。
5. **挂载反馈**：Conductor Mode 使用 `DiffComment` 将唯一 Finding 挂载到 Checks；Git fallback 只在 Chat 中记录，不伪造 Conductor 评论。
6. **修复**：对本轮 Findings 实施最小根因修复。若修复需要产品取舍、扩大范围或修改外部系统，停止并请求决策。
7. **验证**：先运行与改动最相关的测试、Lint、类型检查或静态检查，再运行仓库允许的更广检查；遵守仓库时间预算，无规定时将本地检查总时长控制在 3 分钟以内，超时如实报告。验证命令必须成功退出且覆盖修改行为；不得通过删测试或放宽断言制造绿灯。
8. **重新 Review**：修复后重新获取 Diff 和评论，再进入下一轮；禁止只检查工作树“看起来干净”。

Review 与 Fix 使用不同职责：有可用的独立 reviewer/Subagent 且获得委派许可时，让只读 reviewer 评估最新 Diff，由主 Agent 修复；无此能力时分离两个阶段，不声称经过独立审查。审查必须覆盖修复与其相邻契约（调用方、文档、示例、测试），不只验证上一轮 Findings。

## 收敛与停止

默认最多执行 8 轮；一次完整的 Diff Review 计为一轮，验证失败后不能在同一轮里无限重试 Fix，必须回到新的 Review 并计数。提前停止条件如下：

- 当前 Diff 中不再有明确值得修复的 Finding；
- 同一根因在尝试修复后再次出现（路径、失败模式与触发场景识别身份，行号只作定位）；
- 连续两轮没有新增进展；
- Diff、Review 工具、测试环境或权限不可用；
- 修复需要超出当前 Review 范围的产品、架构或安全决策。

正常收敛必须满足：最后一次完整 Review 无 Finding、必要验证有效通过、该 Review 之后没有再改文件。第 8 轮仍有 Finding 时可做本轮安全修复和验证，但因预算不足不能再 Review，必须有界停止并标注“最后修改尚未复审”，不能宣称收敛。无 Finding 且未修改代码时无需为了形式补跑无关测试。

停止时报告轮数、已修复和未解决 Findings、验证命令/退出状态、覆盖缺口与下一步。环境/权限阻塞不能冒充无 Finding；确证的存量失败也须独立列出并标为阻塞，不擅自扩大修复范围。

## 交付格式

最终 Chat 报告使用以下结构，事实不足时写明“未验证”，不得补写推测：

```text
Review 状态：已收敛 / 有界停止 / 阻塞
运行 Mode：Conductor / Git fallback
Review 轮次：N
已修复：Finding 标题、文件位置、验证结果
剩余问题：Finding 或“无明确值得修复的缺陷”
验证证据：命令与结果
下一步：仅列出用户需要决定或执行的事项
```

详细的 Finding 判定、评论格式和状态转移见 [Review Contract](references/review-contract.md)。
