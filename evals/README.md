# `review-once` Evals

这些评测资产用于验证 Skill 的触发准确率和输出行为，不参与运行时循环，也不应包含真实 Repo 凭证、Cookie、Token 或用户数据。

## Output eval

`evals.json` 覆盖：

- Conductor Mode 的 Diff → Comment → Fix → Verify → Re-review；
- Git fallback Mode 的 base 探测和双份 Diff；
- 初始无 Finding 时立即收敛；
- 修复后继续下一轮；
- 重复 Finding、连续无进展和第 8 轮的有界停止；
- 验证失败时不宣称完成。

每条用例都应以 transcript、工具调用记录、Diff 或测试输出作为 evidence。不能只凭最终一句“已完成”判定通过。

## Trigger eval

`trigger-evals.json` 使用官方 `run_eval.py` 接受的 JSON array，包含正负交替的 24 条 query。每项包含 `query` 与 `should_trigger`：

- 正例覆盖“反复 Review”“Review request”“Conductor Checks”“自动修复再审查”等同义入口；
- 负例覆盖一次性 Review、解释代码、只跑测试、普通开发、PR 发布和 Release；
- collision case 使用共享的“检查/修复/变更”词汇，但目标是 Security Audit、测试编写或文档审阅。

建议每条 query 重复运行 3 次；正例 trigger rate 应大于 `0.5`，负例应小于 `0.5`。Description 优化时固定 60/40 train/validation 切分，只用 train 失败项改写，按 validation 结果选择版本。官方 Runner 会直接读取数组，不需要额外的 `skill_name` 或 `queries` 包装层。

## 本地校验

```bash
jq empty evals/evals.json
jq empty evals/trigger-evals.json
git diff --check
```

## 本机 Smoke 记录

2026-10-04 在本机执行官方 `run_eval.py` 的 24 条单次 smoke：12 条负例通过、12 条正例未被 Runner 记录，汇总为 `12/24`。单 query trace 同时确认临时 Skill 命令已进入 Claude 的 command registry，但模型先读取 `Review request.md`，未显式调用临时命令对应的 `Skill` tool。该结果属于 Runtime/Runner 触发证据不足，不作为 Trigger accuracy 通过结论；应在支持原生 Skill loader 的 Runtime 中重复运行。
