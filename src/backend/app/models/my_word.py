# -*- coding: utf-8 -*-
# 2026-11-25 - smart-voca - my_words 표(회원이 직접 등록한 "내 단어" + 복습 일정) 모델 (이슈 #24, VOCA-FR-001~004)
# 파일 위치: src/backend/app/models/my_word.py
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, Integer, Numeric, SmallInteger, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BigIntId, UtcDateTime


class MyWord(Base):
    """회원 한 명이 직접 넣은 단어. 공용 words 표와 완전히 따로라서 공용 단어·이용권·학습 계산에 영향이 없다."""

    __tablename__ = "my_words"

    id: Mapped[int] = mapped_column(BigIntId, primary_key=True)
    # 탈퇴하면 이 회원의 내 단어도 함께 지운다(CASCADE)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    headword: Mapped[str] = mapped_column(Text)  # 사용자가 쓴 그대로(대소문자 유지)
    # 같은 단어인지 비교하는 용도: 소문자로 바꾼 값. (user_id, headword_key) 가 UNIQUE
    headword_key: Mapped[str] = mapped_column(Text)
    meaning_ko: Mapped[str] = mapped_column(Text)

    # SM-2 복습 상태(공용 user_words 와 같은 의미). 새로 넣은 단어는 오늘부터 공부 대상이다
    repetitions: Mapped[int] = mapped_column(SmallInteger, default=0)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    ease_factor: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("2.50"))
    next_review_date: Mapped[date] = mapped_column(Date)  # 한국 날짜 기준. 이 날짜가 오늘 이전이면 "복습할 차례"
    last_reviewed_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)

    created_at: Mapped[datetime] = mapped_column(UtcDateTime())
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime())

    __table_args__ = (
        UniqueConstraint("user_id", "headword_key"),  # 같은 회원이 같은 단어를 두 번 가질 수 없다
        CheckConstraint("repetitions >= 0", name="repetitions_non_negative"),
        CheckConstraint("interval_days >= 0", name="interval_days_non_negative"),
        CheckConstraint("ease_factor >= 1.30", name="ease_factor_min"),
    )
