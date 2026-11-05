#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 기존 500개 + 새 15개 묶음(501~2000)을 합쳐 data/words/toeic_2000.csv 를 만든다
# 파일 위치: ai-agent/claude/261105_단어2000확장/script/merge_batches.py
# 실행: src/backend/.venv/Scripts/python.exe ai-agent/claude/261105_단어2000확장/script/merge_batches.py
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
WORK = Path(__file__).resolve().parents[1]
CURRENT_CSV = ROOT / "data" / "words" / "toeic_500.csv"
OUT_CSV = ROOT / "data" / "words" / "toeic_2000.csv"
COLUMNS = ["frequency_rank", "headword", "part_of_speech", "meaning_ko", "example_en", "example_ko"]


def read_rows(path: Path) -> list[list[str]]:
    with open(path, encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file)
        assert next(reader) == COLUMNS, f"{path.name}: 머리글이 다름"
        return list(reader)


def main() -> None:
    rows = read_rows(CURRENT_CSV)  # 기존 1~500 은 한 글자도 바꾸지 않고 그대로 앞에 둔다
    assert len(rows) == 500
    for batch_number in range(1, 16):
        rows += read_rows(WORK / "batches" / f"batch_{batch_number:02d}.csv")
    ranks = [int(row[0]) for row in rows]
    assert ranks == list(range(1, 2001)), "순위가 1~2000 연속이 아님"
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    print(f"{OUT_CSV.relative_to(ROOT)} 작성: {len(rows)}행")


if __name__ == "__main__":
    main()
