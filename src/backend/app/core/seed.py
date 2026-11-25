# -*- coding: utf-8 -*-
# 2026-11-25 - smart-voca - 처음 실행해 words 표가 비어 있으면 단어 CSV 를 자동으로 넣는다 (이슈 #23)
# 파일 위치: src/backend/app/core/seed.py
import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.models.word import Word
from app.services.word_import import import_words, read_word_csv, validate_rows

logger = logging.getLogger("smart_voca.seed")

DEFAULT_WORD_CSV = PROJECT_ROOT / "data" / "words" / "toeic_2000.csv"


def seed_words_if_empty(session: Session) -> int:
    """words 표가 비어 있을 때만 기본 단어를 넣고, 넣은 개수를 돌려준다. 이미 단어가 있으면 아무것도 하지 않는다."""
    if session.scalar(select(func.count()).select_from(Word)):
        return 0
    rows, errors = read_word_csv(DEFAULT_WORD_CSV)
    errors += validate_rows(rows) if rows else []
    if errors:
        # 단어를 못 넣어도 서버는 켜지게 한다(화면에서 단어가 비어 보일 뿐). 원인은 로그로 남긴다.
        logger.error("기본 단어 CSV 검증 실패 %d건: %s", len(errors), errors[:3])
        return 0
    result = import_words(session, rows)
    session.commit()
    logger.info("기본 단어 %d개를 처음 실행 때 넣었습니다.", result["inserted"])
    return result["inserted"]
