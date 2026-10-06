#!/usr/bin/env python3
"""evals JSON 有效性 + schema 断言 + trigger 计数断言。"""
import json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
E = ROOT / "evals" / "evals.json"
T = ROOT / "evals" / "trigger-evals.json"
MODES = {"conductor", "git", "either"}
errors = []

evals = json.loads(E.read_text(encoding="utf-8"))
assert set(evals.keys()) == {"skill_name", "evals"}, f"evals.json 顶层键漂移: {set(evals.keys())}"
assert evals["skill_name"] == "review-once"
for ev in evals["evals"]:
    eid = ev.get("id")
    for field in ("prompt", "expected_output", "expectations"):
        if not ev.get(field):
            errors.append(f"evals.json id={eid}: 字段缺失或为空 {field}")
    if not isinstance(ev.get("expectations"), list) or len(ev["expectations"]) == 0:
        errors.append(f"evals.json id={eid}: expectations 非非空列表")
    if ev.get("mode") not in MODES:
        errors.append(f"evals.json id={eid}: mode 非法 {ev.get('mode')}")
extra = set(ev.keys()) - {"id", "mode", "prompt", "expected_output", "expectations"}
if extra:
    errors.append(f"evals.json 存在 schema 外字段: {extra}")
ids = [ev["id"] for ev in evals["evals"]]
assert ids == sorted(ids) and len(set(ids)) == len(ids), "evals id 非递增唯一"

trig = json.loads(T.read_text(encoding="utf-8"))
assert isinstance(trig, list)
pos = [t for t in trig if t["should_trigger"]]
if not (len(trig) == 25 and len(pos) == 12):
    errors.append(f"trigger 计数漂移: total={len(trig)} pos={len(pos)}（基线 25/12/13）")
for t in trig:
    if set(t.keys()) != {"id", "query", "should_trigger"}:
        errors.append(f"trigger-evals id={t.get('id')}: 字段漂移 {set(t.keys())}")

print(f"[evals] output_evals={len(evals['evals'])} trigger={len(trig)} (pos={len(pos)} neg={len(trig)-len(pos)}) errors={len(errors)}")
for e in errors:
    print("  FAIL:", e)
sys.exit(1 if errors else 0)
