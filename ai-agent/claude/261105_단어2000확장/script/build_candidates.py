#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 단어 2000개 확장용 후보 1,500개 선정 (TSL 미사용분 먼저 + NGSL 순위대로·기능어 제외)
# 파일 위치: ai-agent/claude/261105_단어2000확장/script/build_candidates.py
# 실행: src/backend/.venv/Scripts/python.exe ai-agent/claude/261105_단어2000확장/script/build_candidates.py
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
WORK = Path(__file__).resolve().parents[1]
TSL_CSV = ROOT / "ai-agent" / "uploads" / "TSL" / "TSL_12_stats.csv"
NGSL_CSV = ROOT / "ai-agent" / "uploads" / "NGSL" / "NGSL_12_stats.csv"
CURRENT_CSV = ROOT / "data" / "words" / "toeic_500.csv"
OUT_CSV = WORK / "candidates_1500.csv"
OUT_EXCLUDED = WORK / "excluded_function_words.txt"

TARGET_TOTAL = 1500
TSL_LAST_USED_RANK = 517  # 기존 500개 = TSL 순위 1~517 중 17개 제외 (data/words/README.md)
HEADWORD_PATTERN = re.compile(r"^[a-z]+([ -][a-z]+)*$")

# 기능어(닫힌 품사: 관사·대명사·지시어·의문사·접속사·전치사·조동사·한정사/수량사·기초 수사·부정/지시 부사)
FUNCTION_WORDS = set("""
a an the i me my mine myself you your yours yourself yourselves he him his himself she her hers herself it its itself
we us our ours ourselves they them their theirs themselves this that these those who whom whose which what whatever
whichever whoever whomever and or but so if because as than though although while unless until whether nor
of to in for on with at by from up about into over after under between through during before without within against
among across around behind beside besides beyond despite except inside outside toward towards upon off out down
be have do will would can could shall should may might must ought
some any no every each all both either neither many much more most few less least several other another such same
one two three four five six seven eight nine ten
not there here then when where why how
""".split())


def main() -> None:
    current = {row["headword"].lower() for row in csv.DictReader(open(CURRENT_CSV, encoding="utf-8"))}

    # 1) TSL 순위 518~1250 중 형식 규칙을 통과하는 단어 전부 (순위는 TSL 원본 순서)
    tsl_rows = list(csv.DictReader(open(TSL_CSV, encoding="iso-8859-1")))
    tsl_candidates = []
    tsl_format_skipped = []
    for row in tsl_rows:
        tsl_rank = int(row["TSL Rank"])
        word = row["Word"].strip().lower()
        if tsl_rank <= TSL_LAST_USED_RANK or word in current:
            continue
        if not HEADWORD_PATTERN.match(word):
            tsl_format_skipped.append((tsl_rank, word))
            continue
        tsl_candidates.append({"headword": word, "source": "TSL", "source_rank": tsl_rank, "sfi": row["SFI"]})

    # 2) NGSL: 순위대로 훑으며 기능어·형식 위반·기존 단어를 건너뛰고 부족한 만큼 채운다
    need = TARGET_TOTAL - len(tsl_candidates)
    tsl_words = {c["headword"] for c in tsl_candidates}
    ngsl_candidates, skipped_function = [], []
    for row in csv.DictReader(open(NGSL_CSV, encoding="utf-8")):
        if len(ngsl_candidates) >= need:
            break
        word = row["Lemma"].strip().lower()
        rank = int(row["SFI Rank"])
        if word in current or word in tsl_words:
            continue
        if word in FUNCTION_WORDS:
            skipped_function.append((rank, word))
            continue
        if not HEADWORD_PATTERN.match(word):
            continue
        ngsl_candidates.append({"headword": word, "source": "NGSL", "source_rank": rank, "sfi": row["SFI"]})

    # 3) 학습 순서(대표 결정 2026-11-05): TSL(토익 단어) 전부를 TSL 순서대로, 그 뒤에 NGSL 을 NGSL 순서대로.
    #    SFI 로 섞으면 501번부터 say/go/know 같은 초급 단어가 먼저 나와서 채택하지 않음.
    merged = sorted(tsl_candidates, key=lambda c: c["source_rank"]) + ngsl_candidates

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["frequency_rank", "headword", "source", "source_rank", "sfi"])
        for offset, c in enumerate(merged, start=len(current) + 1):
            writer.writerow([offset, c["headword"], c["source"], c["source_rank"], c["sfi"]])
    OUT_EXCLUDED.write_text(
        "NGSL 순위대로 훑는 동안 기능어라서 건너뛴 단어 (순위, 단어)\n"
        + "\n".join(f"{rank}\t{word}" for rank, word in skipped_function) + "\n", encoding="utf-8")

    last_ngsl = ngsl_candidates[-1]
    print(f"TSL 후보 {len(tsl_candidates)}개 (형식 위반으로 제외: {tsl_format_skipped})")
    print(f"NGSL 후보 {len(ngsl_candidates)}개 (NGSL 순위 {ngsl_candidates[0]['source_rank']}~{last_ngsl['source_rank']}, 기능어 제외 {len(skipped_function)}개)")
    print(f"합계 {len(merged)}개, 서비스 순위 {len(current) + 1}~{len(current) + len(merged)}")


if __name__ == "__main__":
    main()
