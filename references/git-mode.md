# Git fallback Mode

当 Conductor MCP 工具不可用时，使用本 Mode。目标是用 Git 的可重复证据完成同等 Review-Fix loop，而不是模拟 Conductor UI。

## Base branch 探测

用户已指定 base、PR target 或限定 Diff 范围时，优先使用并核验该范围；不得以自动探测覆盖例如 `origin/feature/1.x.x` 的明确选择。否则按以下顺序寻找 Review 基线：

1. `CONDUCTOR_DEFAULT_BRANCH` 对应的远程分支；
2. 当前分支的 upstream；
3. `origin/main`；
4. `origin/master`。

先在目标 Repo 执行 `git rev-parse --show-toplevel` 并验证 Ref，再用 `git merge-base <base> HEAD` 求交点。候选必须存在且有共同祖先；base 与 `HEAD` SHA 相等并不无效，工作区仍可能有待审查修改。`CONDUCTOR_DEFAULT_BRANCH` 只在目标 worktree 与 Conductor workspace 一致时可信。

若 upstream 是当前工作分支的同名远程镜像而不是用户指定的 PR target，跳过它（看 branch/ref 身份而非 SHA），避免漏掉已推送变更。upstream 是否是其他 feature base 无法确定时，停止询问，不猜 `main`。不存在候选或历史无共同祖先时停止，报告 Ref 与原因；初始空 Repo 不强行选择错误基线。

## 取 Diff

先读取摘要，再读取完整 Diff：

```bash
git status --short --branch
git merge-base <base> HEAD
git diff --stat <merge-base> HEAD
git diff <merge-base> HEAD
git diff HEAD
git ls-files --others --exclude-standard
```

分别读取 branch Diff、staged/unstaged Diff 理解变更过程，同时以 `git diff <merge-base> --` 核对当前工作区最终状态，避免把已经撤回的中间版本误报为现存缺陷。`git diff HEAD` 不包含 untracked 文件；必须用 `git ls-files --others --exclude-standard` 枚举、筛选本次新增源码/文档/测试并读取正文（例如 `git diff --no-index -- /dev/null <file>`；退出 1 表示存在差异，不表示工具失败）。不为纳入 Review 而擅自 `git add`。

排除构建缓存、临时文件、凭证和无关变更；无法确认文件归属时报告范围缺口，不静默漏审。每次读 Diff 必须检查命令退出状态，读取错误不能当成空 Diff。

## 相关上下文与验证

1. 读取 `Review request.md`、`AGENTS.md`、项目 README 和变更涉及的上下游代码。
2. 从 Repo 的 manifest、Makefile、Conductor settings 或 CI 配置识别已有测试入口；优先运行与改动文件最相关的最小命令。
3. 不擅自安装依赖、不删除数据、不修改锁文件、不切换用户凭证。
4. 若测试失败，先判断是本轮修复引入、已有失败，还是环境缺失；没有证据时标记为 `blocked`，不能宣称通过。

## Fallback 循环

每轮执行：

1. 记录 base、`HEAD`、工作区状态和 Diff 摘要。
2. 审查完整 Diff，逐项覆盖四个[审查镜头](./review-contract.md#审查镜头)，并按 [Review Contract](./review-contract.md) 生成唯一 Findings。
3. 在 Chat 中报告 Findings；Git fallback 不调用不存在的 `DiffComment`，也不向 GitHub 发布评论。
4. 首次修改某个 BASELINE 时已存在的文件前，按[修复 Delta](./review-contract.md#修复-delta)把它快照到仓库之外的临时目录；然后直接做最小根因修复。
5. 运行相关验证并记录退出状态。
6. 重新计算并核对 merge-base，获取最终 Diff、`git diff HEAD` 和 untracked 列表，并按快照求出修复 Delta 作“修复回归”镜头的输入。
7. 自审有 Finding 则回到步骤 1 开始下一轮（四个镜头全量覆盖，修复回归镜头对照 Delta）；自审无 Finding 时直接进入**收敛门**：委派 fresh-context 只读 reviewer，按[盲审信息包](./review-contract.md#盲审信息包)独立复审（Diff、untracked 文件正文与修复 Delta 由主 Agent 取好后提供）。reviewer 报告 Finding 且认定真实则回到步骤 3（先在 Chat 报告再修复）；认为是误报则不改代码，按[误报复核](./review-contract.md#误报复核)进入 DISPUTED；无 Finding 且收敛 Review 之后未再改文件才可收敛。无法委派时按[降级协议](./review-contract.md#降级协议)标「自审收敛」。

若分支在循环中被用户外部改写，重新计算 merge-base 并在 Chat 中报告基线变化；不要继续使用旧 Diff。

## 输出证据

最终报告至少包含：

- 实际采用的 base Ref，而不是只写“默认分支”；
- `git diff --stat` 的变更范围；
- 每个修复对应的验证命令和结果；
- 最后一次 Review 是否仍有 Finding；
- 未运行的验证及其原因。
