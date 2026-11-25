# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - review_logs 표(학습 기록) 모델 (데이터 설계서 4.4, DD-1·DD-2, FR-SRS-03)
# 파일 위치: src/backend/app/models/review_log.py
from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, Index, SmallInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.timeutil import now_utc
from app.models.base import Base, BigIntId, UtcDateTime


class ReviewLog(Base):
    """답할 때마다 행 하나가 추가된다. 고치거나 지우지 않는다(이력)."""

    __tablename__ = "review_logs"

    id: Mapped[int] = mapped_column(BigIntId, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    word_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("words.id"))

    # flashcard 또는 quiz
    activity_type: Mapped[str] = mapped_column(Text)
    # flashcard: dont_know/unsure/know, quiz: correct/wrong/revealed
    result: Mapped[str] = mapped_column(Text)
    # 사용한 최고 힌트 단계 (VS-4 에서 사용. 플래시카드는 0)
    max_hint_level: Mapped[int] = mapped_column(SmallInteger, server_default="0")
    # SM-2 에 반영한 점수. 변환 규칙이 나중에 바뀌어도 "그때 점수"를 확인할 수 있다
    sm2_quality: Mapped[int] = mapped_column(SmallInteger)

    reviewed_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=now_utc, server_default=func.now())
    # 학습한 한국 날짜 (연속 학습일 계산용)
    study_date: Mapped[date] = mapped_column(Date)

    __table_args__ = (
        Index("ix_review_logs_user_id_study_date", "user_id", "study_date"),
        CheckConstraint("activity_type IN ('flashcard', 'quiz')", name="activity_type_allowed"),
        CheckConstraint(
            "result IN ('dont_know', 'unsure', 'know', 'correct', 'wrong', 'revealed')", name="result_allowed"
        ),
        # 활동과 결과값이 맞지 않는 조합(플래시카드인데 correct 등)을 막는다
        CheckConstraint(
            "(activity_type = 'flashcard' AND result IN ('dont_know', 'unsure', 'know'))"
            " OR (activity_type = 'quiz' AND result IN ('correct', 'wrong', 'revealed'))",
            name="activity_result_match",
        ),
        CheckConstraint("max_hint_level BETWEEN 0 AND 3", name="max_hint_level_range"),
        CheckConstraint("sm2_quality BETWEEN 0 AND 5", name="sm2_quality_range"),
    )
