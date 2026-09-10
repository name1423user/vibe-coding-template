#!/usr/bin/env python3
"""原稿の規律を検査する。章を書き終えたら必ず実行し、指摘をすべて潰してから終える。

使い方:
    python scripts/check.py              # 全ファイル
    python scripts/check.py manuscript/part2/phase0-brainstorm.md
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 読者を追い詰める語・逃げる語
BANNED = [
    "簡単です", "簡単に", "すぐできます", "するだけです", "だけでOK",
    "誰でもできます", "難しくありません",
]
HEDGES = [
    "かもしれません", "場合もあります", "かと思います", "だと思われます",
    "などがあります",
]

PHASE_SECTIONS = [
    "## このフェーズの目的",
    "## 成果物",
    "## 手順",
    "## AIへのプロンプト雛形",
    "## 完了条件",
    "## よくある失敗と戻り先",
]

# 完了条件の項目は「確認可能な行動」で終わること
VAGUE_CHECK_ENDINGS = ["理解する", "理解している", "把握する", "意識する", "気をつける"]


def unwritten(text: str) -> bool:
    return "<!-- 未執筆" in text


def check_file(path: Path):
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)
    issues = []

    if unwritten(text):
        return [(rel, "未執筆", "スタブのまま。執筆時にこのコメントを消す")]

    for line_no, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("<!--", "|")):
            continue
        for word in BANNED:
            if word in line:
                issues.append((rel, f"{line_no}行", f"禁止語『{word}』"))
        for word in HEDGES:
            if word in line:
                issues.append((rel, f"{line_no}行", f"曖昧表現『{word}』断定して書く"))

    # 第2部フェーズ章は6節必須
    if "part2" in str(rel):
        for section in PHASE_SECTIONS:
            if section not in text:
                issues.append((rel, "構成", f"節が欠けている: {section}"))

        # プロンプト雛形は引用ブロックで書く
        m = re.search(r"## AIへのプロンプト雛形\n(.*?)(?=\n## |\Z)", text, re.S)
        if m and not m.group(1).strip().startswith(">"):
            issues.append((rel, "構成", "プロンプト雛形が引用ブロック(>)になっていない"))

        # 完了条件は5項目以下
        m = re.search(r"## 完了条件\n(.*?)(?=\n## |\Z)", text, re.S)
        if m:
            items = [l for l in m.group(1).splitlines() if l.strip().startswith("- ")]
            if len(items) > 5:
                issues.append((rel, "構成", f"完了条件が{len(items)}項目。5個以下に絞る"))
            for item in items:
                for ending in VAGUE_CHECK_ENDINGS:
                    if item.rstrip("。 ").endswith(ending):
                        issues.append(
                            (rel, "完了条件", f"確認できない項目: {item.strip()}")
                        )

    # 見出し直後の箇条書き
    lines = text.splitlines()
    for i, line in enumerate(lines[:-1]):
        if line.startswith("#") and lines[i + 1].strip().startswith(("- ", "1. ")):
            issues.append((rel, f"{i + 2}行", "見出しの直後が箇条書き。1文入れる"))

    return issues


def check_running_example():
    path = ROOT / "shared/running-example.md"
    if "**未確定。**" in path.read_text(encoding="utf-8"):
        written = [
            p for p in (ROOT / "manuscript/part2").glob("*.md")
            if not unwritten(p.read_text(encoding="utf-8"))
        ]
        if written:
            return [(
                Path("shared/running-example.md"),
                "前提",
                "通し課題が未確定のまま第2部が書かれている。先に確定させる",
            )]
    return []


def main():
    targets = [Path(a) for a in sys.argv[1:]]
    if not targets:
        targets = sorted(
            list((ROOT / "manuscript").rglob("*.md"))
            + list((ROOT / "appendix").glob("*.md"))
        )

    all_issues = check_running_example()
    for t in targets:
        p = t if t.is_absolute() else ROOT / t
        all_issues += check_file(p)

    written = [i for i in all_issues if i[1] != "未執筆"]
    stubs = [i for i in all_issues if i[1] == "未執筆"]

    for rel, where, msg in written:
        print(f"{rel}:{where}  {msg}")

    print()
    print(f"未執筆 {len(stubs)}ファイル / 指摘 {len(written)}件")
    return 1 if written else 0


if __name__ == "__main__":
    sys.exit(main())
