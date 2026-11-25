# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - user_words 표(사용자별 단어 학습 상태) 모델 (데이터 설계서 4.3, FR-SRS-01, DD-3)
# 파일 위치: src/backend/app/models/user_word.py
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, Index, Integer, Numeric, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UtcDateTime


class UserWord(Base):
    """회원이 한 번이라도 학습한 단어만 행이 생긴다. 행이 없으면 "새 단어"다."""

    __tablename__ = "user_words"

    # (user_id, word_id) 두 컬럼이 합쳐서 기본 키: 같은 회원이 같은 단어 행을 두 개 가질 수 없다
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    word_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("words.id"), primary_key=True)

    # SM-2 상태값 3개: 연속 성공 횟수 / 현재 복습 간격(일) / 난이도 계수(1.30 이상)
    repetitions: Mapped[int] = mapped_column(SmallInteger, server_default="0")
    interval_days: Mapped[int] = mapped_column(Integer, server_default="0")
    ease_factor: Mapped[Decimal] = mapped_column(Numeric(3, 2), server_default="2.50")

    # 다음 복습 날짜 (한국 날짜 기준, DD-8)
    next_review_date: Mapped[date] = mapped_column(Date)

    first_learned_at: Mapped[datetime] = mapped_column(UtcDateTime())
    last_reviewed_at: Mapped[datetime] = mapped_column(UtcDateTime())

    __table_args__ = (
        # "오늘 복습할 단어 찾기"를 빠르게 하는 색인 (이름: ix_user_words_user_id_next_review_date)
        Index("ix_user_words_user_id_next_review_date", "user_id", "next_review_date"),
        CheckConstraint("repetitions >= 0", name="repetitions_non_negative"),
        CheckConstraint("interval_days >= 0", name="interval_days_non_negative"),
        # SM-2 규칙: 난이도 계수는 1.30 아래로 내려가지 않는다
        CheckConstraint("ease_factor >= 1.30", name="ease_factor_min"),
    )
