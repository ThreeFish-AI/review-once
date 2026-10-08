#!/usr/bin/env python3
"""契约状态词汇出现性矩阵 + 图-契约词汇登记表断言。

不变量（RSI-007）：契约 11 态均须在图示资产可追踪（节点 id/label/sublabel 或边标签）；
终态节点集 = 交付格式四终态；DISPUTED 双出边可追踪；HTML 与 candidate.json 节点集零漂移。
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "references" / "review-contract.md"
RUNTIME = {
    "SKILL.md": ROOT / "SKILL.md",
    "review-contract": CONTRACT,
    "conductor-mode": ROOT / "references" / "conductor-mode.md",
    "git-mode": ROOT / "references" / "git-mode.md",
}
CANDIDATE = ROOT / "docs" / "assets" / "review-once-workflow.candidate.json"
HTML = ROOT / "docs" / "assets" / "review-once-workflow.html"

STATES = ["BASELINE", "REVIEW", "REPORT", "FIX", "VERIFY",
          "CONVERGENCE_GATE", "CONVERGED", "SELF_REVIEWED", "DISPUTED", "BOUNDED_STOP", "BLOCKED"]
FINGERPRINT = ["open", "fixed", "verified", "blocked", "disputed"]
CN_TERMINALS = ["已收敛（独立复审）", "自审收敛", "有界停止", "阻塞"]

texts = {name: p.read_text(encoding="utf-8") for name, p in RUNTIME.items()}
cand = json.loads(CANDIDATE.read_text(encoding="utf-8"))
html = HTML.read_text(encoding="utf-8")
errors = []

# —— 硬断言：契约自身必须完整定义 11 态 + 5 Fingerprint 态 ——
for s in STATES + FINGERPRINT:
    if s not in texts["review-contract"]:
        errors.append(f"契约缺状态定义: {s}")

# —— 硬断言：交付格式的中文四终态在 SKILL.md 与 contract 双处（运行时出口口径） ——
for term in CN_TERMINALS:
    for name in ("SKILL.md", "review-contract"):
        if term not in texts[name]:
            errors.append(f"{name} 缺交付终态口径: {term}")

# —— 硬断言：终态挂载制/回显防循环/audit 模式的新契约词汇跨文档存在（RSI-007 护栏化） ——
NEW_CONTRACT = {
    "SKILL.md": ["终态挂载制"],
    "review-contract": ["终态挂载制", "Checks 面板"],
    "conductor-mode": ["终态挂载", "Checks 面板", "回显", "audit 模式"],
}
for name, kws in NEW_CONTRACT.items():
    for kw in kws:
        if kw not in texts[name]:
            errors.append(f"{name} 缺新契约词汇: {kw}")
# evals 不得静默丢失新行为覆盖（audit 模式 / 回显防循环）
_evals_text = (ROOT / "evals" / "evals.json").read_text(encoding="utf-8")
for kw in ("audit 模式", "回显"):
    if kw not in _evals_text:
        errors.append(f"evals.json 缺新行为覆盖关键词: {kw}")

# —— 图-契约词汇登记表（RSI-007）——
# 契约 11 态必须在图示资产可追踪：节点 id/label/sublabel 或边 label 至少一处出现
# （免责声明仅适用于 CONVERGENCE_GATE：契约自注非终态，以边标签呈现即可追踪）
DIAGRAM_TEXT = json.dumps(cand, ensure_ascii=False)
_traceable = {
    "BASELINE": "request" in DIAGRAM_TEXT and "建立基线 BASELINE" in DIAGRAM_TEXT,
    "REVIEW": any(s["id"] == "review" for s in cand["states"]),
    "REPORT": any(s["id"] == "report" for s in cand["states"]),
    "FIX": any(s["id"] == "fix" for s in cand["states"]),
    "VERIFY": any(s["id"] == "verify" for s in cand["states"]),
    "CONVERGENCE_GATE": "收敛门" in DIAGRAM_TEXT,  # 边标签表示（契约自注非终态，可追踪即可）
    "CONVERGED": any(s["id"] == "converged" for s in cand["states"]),
    "SELF_REVIEWED": any(s["id"] == "self_reviewed" for s in cand["states"]),
    "DISPUTED": any(s["id"] == "disputed" for s in cand["states"]),
    "BOUNDED_STOP": any(s["id"] == "bounded" for s in cand["states"]),
    "BLOCKED": any(s["id"] == "blocked" for s in cand["states"]),
}
for st, ok in _traceable.items():
    if not ok:
        errors.append(f"图示资产缺契约状态的可追踪呈现: {st}")
# DISPUTED 两条出边必须在图上可追踪（RSI-007）
_edges = {(t["from"], t["to"]) for t in cand["transitions"]}
for pair in [("disputed", "converged"), ("disputed", "bounded")]:
    if pair not in _edges:
        errors.append(f"图示缺 DISPUTED 关键转移: {pair[0]}->{pair[1]}")
# 终态集合与交付格式四选一一致（图的终态节点 = 收敛/自审收敛/有界停止/阻塞）
_terminal_nodes = {s["id"] for s in cand["states"] if s["lane"] == "terminal"}
if _terminal_nodes != {"converged", "self_reviewed", "bounded", "blocked"}:
    errors.append(f"图终态节点集与契约四终态不一致: {sorted(_terminal_nodes)}")
# HTML 与 candidate 同步（节点集一致）
_html_nodes = set()
import re as _re
for m in _re.finditer(r'data-node-id="([a-z_]+)"', html):
    _html_nodes.add(m.group(1))
if _html_nodes != {s["id"] for s in cand["states"]}:
    errors.append(f"HTML 与 candidate.json 节点集漂移: {sorted(_html_nodes ^ {s['id'] for s in cand['states']})}")

# —— 现状矩阵打印（漂移对比用） ——
print("[states] 契约 11 态 × 运行时文档覆盖矩阵（●=出现）：")
hdr = f"  {'state':<18}" + "".join(f"{n[:12]:>14}" for n in RUNTIME) + f"{'candidate.json':>16}{'html':>8}"
print(hdr)
for s in STATES:
    row = f"  {s:<18}"
    for name in RUNTIME:
        row += f"{'●':>14}" if re.search(rf"\b{s}\b", texts[name]) else f"{'·':>14}"
    row += f"{'●':>16}" if _traceable[s] else f"{'·':>16}"
    row += f"{'●':>8}" if s in html or s.lower() in html else f"{'·':>8}"
    print(row)
print(f"[states] Fingerprint 5 态: " + ", ".join(f"{s}={'●' if s in texts['review-contract'] else '·'}" for s in FINGERPRINT))
cand_ids = [st["id"] for st in cand["states"]]
print(f"[states] candidate.json 节点({len(cand_ids)}): {', '.join(cand_ids)}")
for e in errors:
    print("  FAIL:", e)
print(f"[states] errors={len(errors)}")
sys.exit(1 if errors else 0)
