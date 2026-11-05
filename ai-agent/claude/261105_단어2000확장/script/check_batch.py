#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 단어 묶음 CSV 한 개를 기존 검증 규칙(word_import)으로 검사하고 후보 목록과 대조한다
# 파일 위치: ai-agent/claude/261105_단어2000확장/script/check_batch.py
# 실행: src/backend/.venv/Scripts/python.exe ai-agent/claude/261105_단어2000확장/script/check_batch.py batches/batch_01.csv
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
WORK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from app.services.word_import import read_word_csv, validate_rows  # noqa: E402


def main() -> int:
    batch_path = WORK / sys.argv[1]
    rows, errors = read_word_csv(batch_path)
    errors += [e for e in validate_rows(rows) if "연속 정수" not in e]  # 묶음은 순위가 중간부터라 연속 검사는 제외
    expected = [(int(r["frequency_rank"]), r["headword"]) for r in csv.DictReader(open(WORK / "candidates_1500.csv", encoding="utf-8"))]
    got = [(row.frequency_rank, row.headword) for row in rows]
    if got:
        first, last = got[0][0], got[-1][0]
        want = [pair for pair in expected if first <= pair[0] <= last]
        if got != want:
            wanted_words = {w for _, w in want}
            got_words = {w for _, w in got}
            errors.append(f"후보 목록과 다름: 빠진 단어 {sorted(wanted_words - got_words)}, 남는 단어 {sorted(got_words - wanted_words)}, 순서/순위 불일치 여부 {sorted(set(want) ^ set(got))[:6]}")
    if errors:
        print(f"실패 {len(errors)}건")
        for error in errors:
            print("  -", error)
        return 1
    print(f"통과: {len(rows)}행 (순위 {got[0][0]}~{got[-1][0]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
