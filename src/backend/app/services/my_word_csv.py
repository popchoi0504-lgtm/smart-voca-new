# -*- coding: utf-8 -*-
# 2026-11-25 - smart-voca - 내 단어 CSV(영단어,뜻) 읽기·검사 (VOCA-FR-003, 이슈 #24)
# 파일 위치: src/backend/app/services/my_word_csv.py
import csv
import io

from app.core.errors import AppError
from app.schemas.my_word import HEADWORD_MAX_LENGTH, MEANING_MAX_LENGTH

EXPECTED_HEADER = ["영단어", "뜻"]
MAX_REPORTED_PROBLEMS = 10


def parse_voca_csv(csv_text: str) -> list[tuple[int, str, str]]:
    """CSV 글자를 (줄 번호, 영단어, 뜻) 목록으로 바꾼다. 하나라도 문제가 있으면 아무것도 넣지 않도록 오류를 낸다.

    - 맨 앞의 BOM(엑셀이 붙이는 표시, \\ufeff)은 지운다. 파일을 직접 읽을 때의 utf-8-sig 와 같은 효과다.
    - 빈 줄은 건너뛴다.
    """
    reader = csv.reader(io.StringIO(csv_text.lstrip("﻿"), newline=""))
    header = next(reader, None)
    if header is None or [cell.strip() for cell in header] != EXPECTED_HEADER:
        raise AppError(422, "CSV_INVALID", "첫 줄은 '영단어,뜻' 이어야 해요.")

    rows: list[tuple[int, str, str]] = []
    problems: list[dict] = []
    for line_number, cells in enumerate(reader, start=2):
        if not any(cell.strip() for cell in cells):
            continue  # 빈 줄
        if len(cells) != 2:
            problems.append({"field": f"{line_number}줄", "message": "열이 2개(영단어,뜻)가 아니에요."})
        else:
            headword, meaning = cells[0].strip(), cells[1].strip()
            if not headword or not meaning:
                problems.append({"field": f"{line_number}줄", "message": "영단어나 뜻이 비어 있어요."})
            elif len(headword) > HEADWORD_MAX_LENGTH or len(meaning) > MEANING_MAX_LENGTH:
                problems.append({"field": f"{line_number}줄", "message": "영단어 또는 뜻이 너무 길어요."})
            else:
                rows.append((line_number, headword, meaning))
        if len(problems) >= MAX_REPORTED_PROBLEMS:
            break  # 오류가 너무 많으면 앞의 몇 개만 보여 준다
    if problems:
        raise AppError(422, "CSV_INVALID", "CSV 에 고쳐야 할 줄이 있어요. 아무것도 가져오지 않았어요.", problems)
    if not rows:
        raise AppError(422, "CSV_INVALID", "가져올 단어가 없어요.")
    return rows
