#!/usr/bin/env python3
"""Markdown 相对链接 + GitHub 风格中文锚点完整性校验。"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
MD_FILES = sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts and ".temp" not in p.parts and ".context" not in p.parts)

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")

def github_anchor(heading: str) -> str:
    s = heading.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s)      # 去标点（保留字母数字 CJK 空格连字符下划线）
    return s.replace(" ", "-")

HEAD_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.M)

def headings_of(path: pathlib.Path) -> set:
    return {github_anchor(m) for m in HEAD_RE.findall(path.read_text(encoding="utf-8"))}

def main() -> int:
    errors, checked = [], 0
    for md in MD_FILES:
        anchors_cache: dict[str, set] = {}
        for text, target in LINK_RE.findall(md.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:")):
                continue  # 外部 URL 不在机械校验范围
            checked += 1
            rel, _, anchor = target.partition("#")
            anchor = anchor.strip()
            dest = (md.parent / rel).resolve() if rel else md
            try:
                dest.relative_to(ROOT)
            except ValueError:
                errors.append(f"{md.relative_to(ROOT)}: 链接越界 {target}")
                continue
            if not dest.exists():
                errors.append(f"{md.relative_to(ROOT)}: 目标不存在 {target}")
                continue
            if anchor:
                if dest.suffix != ".md":
                    continue
                if dest not in anchors_cache:
                    anchors_cache[dest] = headings_of(dest)
                if anchor not in anchors_cache[dest]:
                    errors.append(f"{md.relative_to(ROOT)}: 锚点未命中 {target}")
    print(f"[links] checked={checked} files={len(MD_FILES)} errors={len(errors)}")
    for e in errors:
        print("  FAIL:", e)
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
