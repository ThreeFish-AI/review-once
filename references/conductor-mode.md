# Conductor Mode

当 Conductor MCP 的 Diff/Comments 工具可用时，使用本 Mode。Conductor 的 Checks 面板是默认 Review 反馈载体；不要把内部 Review 评论改发到 GitHub，除非用户明确要求。

## Workspace 身份

先核对目标 `git rev-parse --show-toplevel` 与 `CONDUCTOR_WORKSPACE_PATH` 或当前 Harness 的 workspace 路径。MCP 工具绑定 Conductor 原 workspace，并不会因 shell `cd` 自动切换；路径不同、身份无法证明一致或工具 Diff 明显属于其他 Repo 时，使用 Git fallback，禁止在错误 workspace 发评论、读取终端证据或修复。

工具覆盖不足（如新增 untracked 文件未出现在 Diff）时，在同一目标 Repo 以 Git/文件读取补齐。没有 Repo 身份和最终 Diff 的可信证据时报告阻塞，不“无 Findings 通过”。

## 工具路由

| 阶段 | 工具 | 用法 |
| --- | --- | --- |
| 取变更规模 | `mcp__conductor__GetWorkspaceDiff` | 首先传 `stat: true`，了解变更文件和爆炸半径 |
| 读取具体 Diff | `mcp__conductor__GetWorkspaceDiff` | `file` 使用目标 workspace 下的绝对路径，避免只看摘要 |
| 读取已有评论 | `mcp__conductor__GetDiffComments` | 无参数读取全部；按文件读取单个文件评论 |
| 挂载 Finding | `mcp__conductor__DiffComment` | `comments: [{file, lineNumber, body}]`，Repo 相对路径与当前行号，每个唯一 Finding 一条 |
| 终端证据 | `mcp__conductor__GetTerminalOutput` | 可选补充已有运行脚本输出；实际验证以本轮 shell 命令退出码/输出为准 |

如果工具没有提供必要的内容，先说明缺失项；有完整 Git 信息时才降级到 [Git Mode](./git-mode.md)。

## 每轮流程

1. 调用 `GetWorkspaceDiff({stat: true})`，确认变更规模。
2. 读取用户指定的 Review request 和适用 Repo 规则。
3. 对每个变更文件调用 `GetWorkspaceDiff({file: ...})`，结合上下游代码验证行为。
4. 调用 `GetDiffComments()`，避免重复发布已经存在的 Finding。
5. 按 [Review Contract](./review-contract.md) 逐项覆盖四个[审查镜头](./review-contract.md#审查镜头)，筛选并在 Chat 中先报告 Findings。
6. 对确实存在的 Finding 调用 `DiffComment`，一次只挂载一个唯一问题；评论正文保持简短，不在其中塞入完整修复方案或无关背景。
7. 首次修改某个 BASELINE 时已存在的文件前，按[修复 Delta](./review-contract.md#修复-delta)把它快照到仓库之外的临时目录；然后直接在 workspace 中做最小根因修复。
8. 运行相关测试、Lint、类型检查或静态检查，记录本轮命令退出状态；`GetTerminalOutput` 仅作补充，不能用旧的绿灯替代新验证。
9. 再次获取 stat、具体 Diff 和评论，并按快照求出修复 Delta 作“修复回归”镜头的输入；自审有 Finding 则回到步骤 1 开始下一轮，无 Finding 进入步骤 10。
10. 自审无 Finding 时进入**收敛门**：委派 fresh-context 只读 reviewer，按[盲审信息包](./review-contract.md#盲审信息包)独立复审（因 Conductor 工具绑定原 workspace，信息包中的 Diff 与修复 Delta 需由主 Agent 取好后以文本提供，并包含 untracked 文件）。reviewer 报告 Finding 且认定真实则回到步骤 5（先在 Chat 报告，再挂载、修复）；认为是误报则不改代码、不挂载 `DiffComment`，按[误报复核](./review-contract.md#误报复核)进入 DISPUTED；无 Finding 且收敛 Review 之后未再改文件才可收敛。无法委派时按[降级协议](./review-contract.md#降级协议)标「自审收敛」。验证失败、权限或工具不可用时的出口见[状态机](./review-contract.md#状态机)。

## 定位与评论纪律

- 评论必须指向当前 Diff 中实际存在的行；无法定位时只在 Chat 报告，不伪造行号。
- 一个 Finding 不拆成多条重复评论；多个独立根因不合并成模糊评论。
- 修复后旧评论仍可作为历史证据，但不能直接当作新一轮 Finding；必须检查当前 Diff 是否仍复现。
- `GetDiffComments` 只读评论，不把“读取评论”误当作“评论已解决”。
- 工具无 resolve API 时，在 Chat 标明修复/复核状态，不宣称旧评论已经在 UI 消失。

## Conductor 特有边界

- 不要求用户手动点击 Review 或 Fix；Agent 自己完成工具调用、修改和验证。
- 不通过 Sandbox 浏览器完成 OAuth/SSO；需要真实登录态时遵循用户浏览器和 Repo 的安全协议，并在无法验证时停止。
- Conductor 工具不可用不等于 Review 已通过；只能切换到 Git fallback，或报告阻塞。
