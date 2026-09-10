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


# 「よくある失敗と戻り先」の各エントリから、戻り先（Phase番号・手順番号）を抜き出す。
# 本文の表記ゆれ（「戻り先はPhase Nの手順M。」／「Phase N(の手順M)に戻り」／「〜に戻って」）を吸収する。
DEST_PATTERNS = [
    re.compile(r"戻り先はPhase\s*(\d+)(?:の手順(\d+))?"),
    re.compile(r"Phase\s*(\d+)(?:の手順(\d+))?に戻(?:り|って)"),
]


def find_destination(body: str) -> str:
    dest = None
    for pat in DEST_PATTERNS:
        for m in pat.finditer(body):
            dest = m.groups()
    if not dest:
        return "（本文を参照）"
    num, step = dest
    return f"Phase {num}の手順{step}" if step else f"Phase {num}"


def failures(text: str):
    """(症状, 戻り先) のリストを返す。"""
    body = section(text, "よくある失敗と戻り先")
    entries = re.split(r"\n?\*\*(.+?)\*\*\n", body)
    it = iter(entries[1:])
    for symptom, detail in zip(it, it):
        yield symptom.strip(), find_destination(detail)


def main():
    prompts, checks, troubles = [], [], []

    for title, text in chapters():
        p = section(text, "AIへのプロンプト雛形")
        if p:
            prompts.append(f"## {title}\n\n{p}\n")
        c = section(text, "完了条件")
        if c:
            checks.append(f"## {title}\n\n{c}\n")
        for symptom, dest in failures(text):
            troubles.append(f"| {symptom} | {dest} |")

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
    (ROOT / "appendix/C-troubleshooting.md").write_text(
        "# 付録C トラブルシューティング早見表\n\n" + header
        + "\n各フェーズの「よくある失敗と戻り先」から生成したもの。症状から、戻るべきフェーズを引く。\n\n"
        + "| 症状 | 戻る先 |\n|---|---|\n"
        + "\n".join(troubles) + "\n",
        encoding="utf-8",
    )

    print(
        f"付録A: {len(prompts)}章分  /  付録B: {len(checks)}章分  /  "
        f"付録C: {len(troubles)}件 を生成しました"
    )


if __name__ == "__main__":
    main()
