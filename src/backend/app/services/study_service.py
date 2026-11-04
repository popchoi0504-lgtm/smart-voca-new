# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 새 단어 학습·SM-2 반영·요금제 범위 검사의 업무 규칙 (FR-STUDY-01~06, FR-SRS-01~03, DD-3·DD-5·DD-8)
# 파일 위치: src/backend/app/services/study_service.py
import logging
from datetime import date, datetime, time, timedelta

from sqlalchemy import exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.timeutil import KST, now_utc
from app.core_logic.quality import flashcard_quality
from app.core_logic.sm2 import Sm2State, calculate_next
from app.models.review_log import ReviewLog
from app.models.user import User
from app.models.user_word import UserWord
from app.models.word import Word
from app.schemas.study import FlashcardResponse, NewWordItem, TodayResponse

logger = logging.getLogger("smart_voca.study")

MAX_NEW_WORDS_PER_REQUEST = 10  # 한 세션(약 5분) 분량 (FR-STUDY-06)


def _is_premium(user: User, moment: datetime) -> bool:
    return user.premium_until is not None and user.premium_until > moment


def _plan_word_limit(db: Session, user: User, moment: datetime) -> int:
    """요금제가 허용하는 단어 수. 무료는 설정값(250), 프리미엄은 전체 단어 수(순위 최댓값)."""
    if _is_premium(user, moment):
        return db.scalar(select(func.max(Word.frequency_rank))) or 0
    return get_settings().free_word_limit


def _unlearned_in_plan(user_id: int, plan_limit: int):
    """"요금제 범위 안에서 이 회원이 아직 학습하지 않은 단어" 조건. 행이 없으면 새 단어 (DD-3)."""
    learned = exists().where(UserWord.user_id == user_id, UserWord.word_id == Word.id)
    return (Word.frequency_rank <= plan_limit, ~learned)


def _new_target_count(db: Session, user: User, plan_limit: int, now: datetime) -> tuple[int, int]:
    """(오늘 이미 배운 새 단어 수, 오늘 더 배울 새 단어 수)를 계산한다."""
    today_start = datetime.combine(now.astimezone(KST).date(), time.min, tzinfo=KST)
    learned_today = db.scalar(
        select(func.count())
        .select_from(UserWord)
        .where(UserWord.user_id == user.id, UserWord.first_learned_at >= today_start,
               UserWord.first_learned_at < today_start + timedelta(days=1))
    )
    remaining_in_plan = db.scalar(
        select(func.count()).select_from(Word).where(*_unlearned_in_plan(user.id, plan_limit))
    )
    return learned_today, max(0, min(user.daily_new_limit - learned_today, remaining_in_plan))


def get_today(db: Session, user: User) -> TodayResponse:
    """"오늘 할 것" 요약: 복습 대상 수와 오늘 더 배울 새 단어 수."""
    now = now_utc()
    today = now.astimezone(KST).date()
    plan_limit = _plan_word_limit(db, user, now)
    learned_today, new_target = _new_target_count(db, user, plan_limit, now)
    review_due = db.scalar(
        select(func.count()).select_from(UserWord).where(UserWord.user_id == user.id, UserWord.next_review_date <= today)
    )
    # 요금제 때문에 막힘: 범위 안의 새 단어는 다 배웠는데, 범위 밖에 아직 못 배운 단어가 남아 있는 상태
    remaining_in_plan = db.scalar(select(func.count()).select_from(Word).where(*_unlearned_in_plan(user.id, plan_limit)))
    locked_words = db.scalar(
        select(func.count()).select_from(Word).where(Word.frequency_rank > plan_limit)
    )
    return TodayResponse(
        today=today,
        review_due_count=review_due,
        new_target_count=new_target,
        new_learned_today=learned_today,
        daily_new_limit=user.daily_new_limit,
        plan_word_limit=plan_limit,
        new_locked_by_plan=remaining_in_plan == 0 and locked_words > 0,
    )


def get_new_words(db: Session, user: User, limit: int) -> list[NewWordItem]:
    """새 단어를 빈도 순위가 낮은(자주 나오는) 순서로 min(limit, 오늘 더 배울 수)개 돌려준다."""
    now = now_utc()
    plan_limit = _plan_word_limit(db, user, now)
    _, new_target = _new_target_count(db, user, plan_limit, now)
    count = min(limit, MAX_NEW_WORDS_PER_REQUEST, new_target)
    if count <= 0:
        return []
    words = db.scalars(
        select(Word).where(*_unlearned_in_plan(user.id, plan_limit)).order_by(Word.frequency_rank).limit(count)
    ).all()
    return [
        NewWordItem(
            word_id=word.id, headword=word.headword, part_of_speech=word.part_of_speech,
            meaning_ko=word.meaning_ko, example_en=word.example_en, example_ko=word.example_ko,
            frequency_rank=word.frequency_rank,
        )
        for word in words
    ]


def submit_flashcard(db: Session, user: User, word_id: int, rating: str) -> FlashcardResponse:
    """새 단어 한 개의 평가를 반영한다: user_words 행 생성(SM-2 첫 계산) + review_logs 추가를 한 번에(트랜잭션).

    하루 새 단어 수(daily_new_limit)는 목표치라 여기서 막지 않는다. 요금제 범위는 막는다.
    """
    now = now_utc()
    word = db.get(Word, word_id)
    if word is None:
        raise AppError(404, "WORD_NOT_FOUND", "존재하지 않는 단어입니다.")
    if word.frequency_rank > _plan_word_limit(db, user, now):
        raise AppError(403, "PLAN_LIMIT_EXCEEDED", "무료 요금제에서는 이 단어를 학습할 수 없습니다.")
    already_learned = AppError(409, "WORD_ALREADY_LEARNED", "이미 학습한 단어입니다.")
    if db.get(UserWord, (user.id, word_id)) is not None:
        raise already_learned

    quality = flashcard_quality(rating)
    new_state = calculate_next(Sm2State(), quality)
    today: date = now.astimezone(KST).date()
    next_review_date = today + timedelta(days=new_state.interval_days)
    db.add(UserWord(
        user_id=user.id, word_id=word_id, repetitions=new_state.repetitions, interval_days=new_state.interval_days,
        ease_factor=new_state.ease_factor, next_review_date=next_review_date,
        first_learned_at=now, last_reviewed_at=now,
    ))
    db.add(ReviewLog(
        user_id=user.id, word_id=word_id, activity_type="flashcard", result=rating, max_hint_level=0,
        sm2_quality=quality, reviewed_at=now, study_date=today,
    ))
    try:
        db.commit()  # 두 표가 함께 저장되거나, 함께 저장되지 않는다
    except IntegrityError:
        # 위 확인과 저장 사이에 같은 카드가 동시에 제출된 경우: DB 의 기본 키 제약이 최후의 방어선
        db.rollback()
        raise already_learned from None
    logger.info("플래시카드 평가 user_id=%s word_id=%s rating=%s", user.id, word_id, rating)
    return FlashcardResponse(
        word_id=word_id, sm2_quality=quality, interval_days=new_state.interval_days, next_review_date=next_review_date
    )


def update_daily_new_limit(db: Session, user: User, daily_new_limit: int) -> User:
    """하루 새 단어 수 설정을 바꾼다."""
    user.daily_new_limit = daily_new_limit
    db.commit()
    db.refresh(user)
    logger.info("설정 변경 user_id=%s daily_new_limit=%s", user.id, daily_new_limit)
    return user
