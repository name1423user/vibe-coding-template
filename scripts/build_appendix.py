#!/usr/bin/env python3
"""付録A（プロンプト集）と付録B（チェックリスト一括）を第2部の各章から生成する。

付録を手書きすると本文と揺れる。必ずこのスクリプトで再生成する。

使い方:
    python scripts/build_appendix.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PART2 = ROOT / "manuscript/part2"


def section(text: str, heading: str) -> str:
    m = re.search(rf"## {re.escape(heading)}\n(.*?)(?=\n## |\Z)", text, re.S)
    return m.group(1).strip() if m else ""


def chapters():
    for path in sorted(PART2.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if "<!-- 未執筆" in text:
            continue
        title = text.splitlines()[0].lstrip("# ").strip()
        yield title, text


def main():
    prompts, checks = [], []

    for title, text in chapters():
        p = section(text, "AIへのプロンプト雛形")
        if p:
            prompts.append(f"## {title}\n\n{p}\n")
        c = section(text, "完了条件")
        if c:
            checks.append(f"## {title}\n\n{c}\n")

    header = "<!-- 自動生成。手書きしない。python scripts/build_appendix.py で再生成する。 -->\n"

    (ROOT / "appendix/A-prompts.md").write_text(
        "# 付録A プロンプト集\n\n" + header
        + "\n本文中のプロンプト雛形をフェーズ順に集めたもの。コピーして使う。\n\n"
        + "\n".join(prompts),
        encoding="utf-8",
    )
    (ROOT / "appendix/B-checklists.md").write_text(
        "# 付録B チェックリスト一括\n\n" + header
        + "\n各フェーズの完了条件をまとめたもの。進行中はこのページを開いておく。\n\n"
        + "\n".join(checks),
        encoding="utf-8",
    )

    print(f"付録A: {len(prompts)}章分  /  付録B: {len(checks)}章分 を生成しました")


if __name__ == "__main__":
    main()
