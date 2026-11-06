# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 학습 기록 요약(오늘 학습량·누적·연속 학습일·숙련도 분포) 계산 (FR-PROG-02~05, DD-3·DD-8)
# 파일 위치: src/backend/app/services/progress_service.py
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.timeutil import KST, now_utc
from app.core_logic.progress_rules import FAMILIAR_INTERVAL_DAYS, calculate_streak, classify_mastery
from app.models.review_log import ReviewLog
from app.models.user import User
from app.models.user_word import UserWord
from app.models.word import Word
from app.schemas.progress import (
    LearnedWordItem,
    LearnedWordsResponse,
    MasteryCounts,
    ProgressSummaryResponse,
    TodayProgress,
)


def get_summary(db: Session, user: User) -> ProgressSummaryResponse:
    """학습 기록 요약. 저장된 요약값 없이 매번 기록(review_logs)·상태(user_words)에서 계산한다(DD-3)."""
    today = now_utc().astimezone(KST).date()  # 사용자의 "하루"는 한국 시간 기준 (DD-8)

    reviewed_count, new_learned_count = db.execute(
        select(
            func.count(func.distinct(ReviewLog.word_id)),
            func.count(func.distinct(case((ReviewLog.activity_type == "flashcard", ReviewLog.word_id)))),
        ).where(ReviewLog.user_id == user.id, ReviewLog.study_date == today)
    ).one()

    study_dates = db.scalars(select(func.distinct(ReviewLog.study_date)).where(ReviewLog.user_id == user.id)).all()

    total_learned_count, familiar_count = db.execute(
        select(
            func.count(),
            func.count(case((UserWord.interval_days >= FAMILIAR_INTERVAL_DAYS, 1))),
        ).where(UserWord.user_id == user.id)
    ).one()
    total_word_count = db.scalar(select(func.count()).select_from(Word))

    return ProgressSummaryResponse(
        today=TodayProgress(date=today, reviewed_count=reviewed_count, new_learned_count=new_learned_count),
        total_learned_count=total_learned_count,
        total_word_count=total_word_count,
        current_streak_days=calculate_streak(study_dates, today),
        mastery=MasteryCounts(
            new_count=max(0, total_word_count - total_learned_count),
            learning_count=total_learned_count - familiar_count,
            familiar_count=familiar_count,
        ),
    )


def get_learned_words(db: Session, user: User) -> LearnedWordsResponse:
    """내가 배운 단어 전체(최근에 배운 순). user_words 행이 있는 단어가 곧 "배운 단어"다(DD-3).
    다른 회원의 단어가 섞이지 않도록 반드시 user_id 로 거른다. 전체 단어가 2,000개라 쪽 나누기는 하지 않는다."""
    rows = db.execute(
        select(Word, UserWord.interval_days, UserWord.first_learned_at)
        .join(UserWord, UserWord.word_id == Word.id)
        .where(UserWord.user_id == user.id)
        .order_by(UserWord.first_learned_at.desc(), Word.id.desc())
    ).all()
    items = [
        LearnedWordItem(
            word_id=word.id,
            headword=word.headword,
            part_of_speech=word.part_of_speech,
            meaning_ko=word.meaning_ko,
            example_en=word.example_en,
            example_ko=word.example_ko,
            mastery=classify_mastery(interval_days),
            first_learned_date=first_learned_at.astimezone(KST).date(),
        )
        for word, interval_days, first_learned_at in rows
    ]
    return LearnedWordsResponse(total_count=len(items), items=items)
