# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - words 표(단어) 모델 (데이터 설계서 4.2, FR-WORD-01~06, DD-5)
# 파일 위치: src/backend/app/models/word.py
from sqlalchemy import BigInteger, CheckConstraint, Identity, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Word(Base):
    __tablename__ = "words"

    # 번호표(기본 키). 나중에 user_words 가 이 번호로 단어를 가리킨다
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)

    # 영단어(소문자). UNIQUE: 시드를 다시 실행할 때 "이미 있는 단어인가"를 이 값으로 판단한다
    headword: Mapped[str] = mapped_column(Text, unique=True)

    # 품사 (n. v. adj. adv. prep. conj. phr.)
    part_of_speech: Mapped[str] = mapped_column(Text)

    meaning_ko: Mapped[str] = mapped_column(Text)

    # 영어 예문. 퀴즈에서 단어 부분을 ____ 로 가리므로 단어가 그대로 들어 있어야 한다
    example_en: Mapped[str] = mapped_column(Text)

    example_ko: Mapped[str] = mapped_column(Text)

    # 학습 순서(1 이 먼저). 250 이하는 무료로 "계산"한다 (별도 컬럼 없음, DD-5)
    frequency_rank: Mapped[int] = mapped_column(Integer, unique=True)

    __table_args__ = (
        # 이름: ck_words_frequency_rank_positive
        CheckConstraint("frequency_rank >= 1", name="frequency_rank_positive"),
    )
