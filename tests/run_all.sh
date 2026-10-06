#!/bin/bash
# 仓库护栏校验总入口：evals JSON/schema、Markdown 链接锚点、状态词汇矩阵、git diff --check
set -u
TESTS=$(cd "$(dirname "$0")" && pwd)
REPO=$(git rev-parse --show-toplevel)
cd "$REPO" || exit 1
rc=0

echo "== 护栏: evals JSON 与 schema =="
jq empty evals/evals.json && jq empty evals/trigger-evals.json || rc=1
python3 "$TESTS/check_evals.py" || rc=1

echo "== 护栏: Markdown 链接与锚点 =="
python3 "$TESTS/check_links.py" || rc=1

echo "== 护栏: 状态词汇矩阵 =="
python3 "$TESTS/check_states.py" || rc=1

echo "== 护栏: git diff --check =="
git diff --check && echo "[gitdiff] clean" || rc=1

if [ "$rc" -eq 0 ]; then echo "== ALL GREEN =="; else echo "== RED (rc=$rc) =="; fi
exit $rc
