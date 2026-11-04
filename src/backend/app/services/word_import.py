# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 단어 CSV 읽기·검증·적재(upsert) (FR-WORD-01~06, 구현 계획서 VS-2)
# 파일 위치: src/backend/app/services/word_import.py
import csv
import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.word import Word

EXPECTED_COLUMNS = ["frequency_rank", "headword", "part_of_speech", "meaning_ko", "example_en", "example_ko"]
ALLOWED_PARTS_OF_SPEECH = {"n.", "v.", "adj.", "adv.", "prep.", "conj.", "phr."}
HEADWORD_PATTERN = re.compile(r"^[a-z]+([ -][a-z]+)*$")  # 소문자, 공백, 하이픈만
MAX_MEANING_LENGTH = 60
MAX_EXAMPLE_KO_LENGTH = 100
EXAMPLE_EN_WORD_RANGE = (6, 16)
# 순위 바꿔치기 충돌을 피하려고 임시로 밀어 두는 크기 (frequency_rank 가 UNIQUE 라서 필요)
TEMPORARY_RANK_OFFSET = 1_000_000


class WordImportError(Exception):
    """검증 실패·적재 불가. 메시지에 줄 번호가 포함된다."""


@dataclass
class WordRow:
    line_number: int  # CSV 파일의 줄 번호 (머리글이 1줄)
    frequency_rank: int
    headword: str
    part_of_speech: str
    meaning_ko: str
    example_en: str
    example_ko: str


def read_word_csv(csv_path: Path) -> tuple[list[WordRow], list[str]]:
    """CSV 를 읽어 (행 목록, 오류 목록) 을 돌려준다. 열 구성이 틀리면 더 진행하지 않는다."""
    errors: list[str] = []
    rows: list[WordRow] = []
    with open(csv_path, encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file)
        header = next(reader, None)
        if header != EXPECTED_COLUMNS:
            return [], [f"1줄: 머리글이 {EXPECTED_COLUMNS} 와 다름 (실제: {header})"]
        for line_number, cells in enumerate(reader, start=2):
            if len(cells) != len(EXPECTED_COLUMNS):
                errors.append(f"{line_number}줄: 열이 {len(cells)}개 (6개여야 함)")
                continue
            cells = [cell.strip() for cell in cells]
            if not all(cells):
                errors.append(f"{line_number}줄: 빈 값이 있음")
                continue
            if not cells[0].isdigit():
                errors.append(f"{line_number}줄: frequency_rank 가 정수가 아님 ({cells[0]})")
                continue
            rows.append(WordRow(line_number, int(cells[0]), *cells[1:]))
    return rows, errors


def example_contains_headword(example_en: str, headword: str) -> bool:
    """예문에 단어가 활용 없이 그대로 있는지 (대소문자 무시, 영문자 경계 기준). 퀴즈 빈칸 처리의 전제."""
    pattern = r"(?<![A-Za-z])" + re.escape(headword) + r"(?![A-Za-z])"
    return re.search(pattern, example_en, re.IGNORECASE) is not None


def validate_rows(rows: list[WordRow]) -> list[str]:
    """행 하나씩의 규칙과 전체 규칙(중복·순위 연속)을 검사해 오류 목록을 돌려준다."""
    errors: list[str] = []
    seen_headwords: dict[str, int] = {}
    for row in rows:
        where = f"{row.line_number}줄({row.headword})"
        if not HEADWORD_PATTERN.match(row.headword):
            errors.append(f"{where}: headword 는 소문자 영문자·공백·하이픈만 가능")
        if row.headword in seen_headwords:
            errors.append(f"{where}: headword 중복 ({seen_headwords[row.headword]}줄과 같음)")
        seen_headwords.setdefault(row.headword, row.line_number)
        if row.part_of_speech not in ALLOWED_PARTS_OF_SPEECH:
            errors.append(f"{where}: 품사 '{row.part_of_speech}' 는 허용 목록에 없음")
        if len(row.meaning_ko) > MAX_MEANING_LENGTH:
            errors.append(f"{where}: meaning_ko 가 {MAX_MEANING_LENGTH}자 초과")
        if len(row.example_ko) > MAX_EXAMPLE_KO_LENGTH:
            errors.append(f"{where}: example_ko 가 {MAX_EXAMPLE_KO_LENGTH}자 초과")
        word_count = len(row.example_en.split())
        if not EXAMPLE_EN_WORD_RANGE[0] <= word_count <= EXAMPLE_EN_WORD_RANGE[1]:
            errors.append(f"{where}: example_en 이 {word_count}단어 ({EXAMPLE_EN_WORD_RANGE[0]}~{EXAMPLE_EN_WORD_RANGE[1]}단어여야 함)")
        if not example_contains_headword(row.example_en, row.headword):
            errors.append(f"{where}: example_en 에 '{row.headword}' 가 그대로 들어 있지 않음")
    # 순위는 1~N 이 중복·누락 없이 있어야 한다
    ranks = sorted(row.frequency_rank for row in rows)
    if ranks != list(range(1, len(rows) + 1)):
        errors.append(f"frequency_rank 가 1~{len(rows)} 연속 정수가 아님 (중복 또는 누락)")
    return errors


def import_words(session: Session, rows: list[WordRow]) -> dict[str, int]:
    """headword 기준 upsert. 호출한 쪽이 commit 해야 반영된다(한 트랜잭션).
    DB 에만 있는 단어가 있으면 조용히 두지 않고 오류를 낸다(user_words 가 참조하므로 삭제하지 않는다)."""
    csv_headwords = {row.headword for row in rows}
    existing_words = {word.headword: word for word in session.scalars(select(Word))}
    only_in_db = sorted(set(existing_words) - csv_headwords)
    if only_in_db:
        raise WordImportError(f"DB 에는 있고 CSV 에는 없는 단어: {only_in_db}")
    # 1단계: 순위가 바뀌는 기존 단어를 임시 순위로 밀어 UNIQUE 충돌을 피한다
    for row in rows:
        existing = existing_words.get(row.headword)
        if existing is not None and existing.frequency_rank != row.frequency_rank:
            existing.frequency_rank = TEMPORARY_RANK_OFFSET + existing.frequency_rank
    session.flush()
    # 2단계: 최종 값으로 갱신하거나 새로 넣는다
    inserted = updated = 0
    for row in rows:
        existing = existing_words.get(row.headword)
        if existing is None:
            session.add(Word(headword=row.headword, part_of_speech=row.part_of_speech, meaning_ko=row.meaning_ko,
                             example_en=row.example_en, example_ko=row.example_ko, frequency_rank=row.frequency_rank))
            inserted += 1
        else:
            existing.part_of_speech, existing.meaning_ko = row.part_of_speech, row.meaning_ko
            existing.example_en, existing.example_ko = row.example_en, row.example_ko
            existing.frequency_rank = row.frequency_rank
            updated += 1
        session.flush()
    return {"inserted": inserted, "updated": updated}
