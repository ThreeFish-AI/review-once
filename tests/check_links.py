#!/usr/bin/env python3
"""Markdown 相对链接 + GitHub 风格中文锚点完整性校验。"""
import re, sys, pathlib, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXCLUDE = {".git", ".temp", ".context"}

def md_files(root: pathlib.Path) -> list:
    # 按仓库相对路径排除：只滤仓内临时物，不受仓库所在父路径影响（RSI-012）
    return sorted(p for p in root.rglob("*.md") if not EXCLUDE & set(p.relative_to(root).parts))

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")

def github_anchor(heading: str) -> str:
    s = heading.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s)      # 去标点（保留字母数字 CJK 空格连字符下划线）
    return s.replace(" ", "-")

HEAD_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.M)

def headings_of(path: pathlib.Path) -> set:
    return {github_anchor(m) for m in HEAD_RE.findall(path.read_text(encoding="utf-8"))}

def check(root: pathlib.Path) -> tuple:
    files, errors, checked = md_files(root), [], 0
    if not files:
        errors.append("未扫描到任何 Markdown 文件（链接门空转）")
    for md in files:
        anchors_cache: dict[str, set] = {}
        for text, target in LINK_RE.findall(md.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:")):
                continue  # 外部 URL 不在机械校验范围
            checked += 1
            rel, _, anchor = target.partition("#")
            anchor = anchor.strip()
            dest = (md.parent / rel).resolve() if rel else md
            try:
                dest.relative_to(root)
            except ValueError:
                errors.append(f"{md.relative_to(root)}: 链接越界 {target}")
                continue
            if not dest.exists():
                errors.append(f"{md.relative_to(root)}: 目标不存在 {target}")
                continue
            if anchor:
                if dest.suffix != ".md":
                    continue
                if dest not in anchors_cache:
                    anchors_cache[dest] = headings_of(dest)
                if anchor not in anchors_cache[dest]:
                    errors.append(f"{md.relative_to(root)}: 锚点未命中 {target}")
    return checked, len(files), errors

def self_test() -> list:
    """回归（RSI-012）：仓库位于 .temp 祖先下仍须扫到并报出死链；仓内 .temp 仍排除。"""
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp).resolve() / ".temp" / "fake" / "repo"
        (root / ".temp").mkdir(parents=True)
        (root / "a.md").write_text("[dead](./missing.md)\n", encoding="utf-8")
        (root / ".temp" / "b.md").write_text("[dead](./missing.md)\n", encoding="utf-8")
        got = check(root)
    if (got[0], got[1], len(got[2])) != (1, 1, 1):
        return [f"self-test: .temp 祖先下 checked={got[0]} files={got[1]} errors={len(got[2])}（期望 1/1/1）"]
    return []

def main() -> int:
    fails = self_test()
    checked, files, errors = check(ROOT)
    errors = fails + errors
    print(f"[links] checked={checked} files={files} errors={len(errors)} selftest={'fail' if fails else 'ok'}")
    for e in errors:
        print("  FAIL:", e)
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
