# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 복습 퀴즈 문제 목록·힌트·답 제출의 업무 규칙 (FR-QUIZ-01~03, FR-HINT-01~05, FR-SRS-02~05, IF-4·IF-5)
# 파일 위치: src/backend/app/services/quiz_service.py
import logging
import re
from datetime import date, timedelta

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.timeutil import KST, now_utc
from app.core_logic.hints import letter_count, make_seed, mask, scramble
from app.core_logic.quality import quiz_quality
from app.core_logic.sm2 import Sm2State, calculate_next
from app.models.review_log import ReviewLog
from app.models.user import User
from app.models.user_word import UserWord
from app.models.word import Word
from app.schemas.quiz import AnswerResponse, HintResponse, QuizItem, QuizQueueResponse

logger = logging.getLogger("smart_voca.quiz")

MAX_QUEUE_SIZE = 10  # 한 세션 분량 (FR-SRS-05)
BLANK_IN_EXAMPLE = "______"


def _today() -> date:
    return now_utc().astimezone(KST).date()


def _due_count(db: Session, user_id: int, today: date) -> int:
    return db.scalar(
        select(func.count()).select_from(UserWord).where(UserWord.user_id == user_id, UserWord.next_review_date <= today)
    )


def _mask_example(headword: str, example_en: str) -> str | None:
    """예문의 영단어를 ______ 로 가린다. 예문에 단어가 없으면 None(가릴 수 없으니 화면이 예문을 쓰지 않는다)."""
    masked, count = re.subn(re.escape(headword), BLANK_IN_EXAMPLE, example_en, flags=re.IGNORECASE)
    return masked if count else None


def _get_learned_word(db: Session, user: User, word_id: int) -> Word:
    """퀴즈 대상 단어. 없으면 404, 아직 학습하지 않은 단어면 409(user_words 행이 있어야 "배운 단어")."""
    word = db.get(Word, word_id)
    if word is None:
        raise AppError(404, "WORD_NOT_FOUND", "존재하지 않는 단어입니다.")
    if db.get(UserWord, (user.id, word_id)) is None:
        raise AppError(409, "WORD_NOT_LEARNED", "아직 학습하지 않은 단어입니다.")
    return word


def get_queue(db: Session, user: User, limit: int) -> QuizQueueResponse:
    """복습 대상을 오래 밀린 순(복습일이 빠른 순)으로 최대 limit 개. 만료된 이용권이어도 배운 단어는 복습 가능(IF-7)."""
    today = _today()
    words = db.scalars(
        select(Word)
        .join(UserWord, UserWord.word_id == Word.id)
        .where(UserWord.user_id == user.id, UserWord.next_review_date <= today)
        .order_by(UserWord.next_review_date, Word.frequency_rank)
        .limit(min(limit, MAX_QUEUE_SIZE))
    ).all()
    items = [
        QuizItem(
            word_id=word.id, part_of_speech=word.part_of_speech, meaning_ko=word.meaning_ko,
            example_masked=_mask_example(word.headword, word.example_en), letter_count=letter_count(word.headword),
        )
        for word in words
    ]
    return QuizQueueResponse(items=items, remaining_due_count=_due_count(db, user.id, today))


def get_hint(db: Session, user: User, word_id: int, level: int) -> HintResponse:
    """힌트 한 단계. 아무것도 저장하지 않고, 같은 날 같은 결과를 돌려준다(IF-5)."""
    word = _get_learned_word(db, user, word_id)
    seed = make_seed(user.id, word_id, _today(), level)
    if level == 1:
        scrambled = scramble(word.headword, seed)
        return HintResponse(level=1, skipped=scrambled is None, scrambled=scrambled)
    if level == 2:
        return HintResponse(level=2, masked=mask(word.headword, seed))
    return HintResponse(level=3, answer=word.headword)


def _judge(word: Word, answer: str | None, max_hint_level: int) -> str:
    """정답 확인(3단계)이면 입력과 상관없이 revealed. 아니면 대소문자·앞뒤 공백을 무시하고 비교."""
    if max_hint_level == 3:
        return "revealed"
    return "correct" if answer.strip().lower() == word.headword.lower() else "wrong"


def submit_answer(db: Session, user: User, word_id: int, answer: str | None, max_hint_level: int) -> AnswerResponse:
    """답을 판정하고, 오늘 첫 제출이면 SM-2 와 기록에 반영한다. 아니면 연습으로 판정만 돌려준다(IF-4)."""
    word = _get_learned_word(db, user, word_id)
    result = _judge(word, answer, max_hint_level)
    today = _today()
    correct_answer = word.headword if result in ("correct", "revealed") else None  # 오답이면 정답을 숨긴다

    # 같은 단어를 동시에 두 번 제출해도 한 번만 반영되도록 user_words 행을 잠그고 확인한다(순서대로 처리됨)
    state_row = db.get(UserWord, (user.id, word_id), with_for_update=True)
    logged_today = db.scalar(
        select(exists().where(
            ReviewLog.user_id == user.id, ReviewLog.word_id == word_id,
            ReviewLog.activity_type == "quiz", ReviewLog.study_date == today,
        ))
    )
    if logged_today or state_row.next_review_date > today:
        db.rollback()  # 잠금 해제
        return AnswerResponse(
            result=result, recorded=False, practice=True, sm2_quality=None, interval_days=None,
            next_review_date=None, correct_answer=correct_answer, remaining_due_count=_due_count(db, user.id, today),
        )

    quality = quiz_quality(result, max_hint_level)
    new_state = calculate_next(
        Sm2State(state_row.repetitions, state_row.interval_days, state_row.ease_factor), quality
    )
    now = now_utc()
    state_row.repetitions = new_state.repetitions
    state_row.interval_days = new_state.interval_days
    state_row.ease_factor = new_state.ease_factor
    state_row.next_review_date = today + timedelta(days=new_state.interval_days)
    state_row.last_reviewed_at = now
    db.add(ReviewLog(
        user_id=user.id, word_id=word_id, activity_type="quiz", result=result, max_hint_level=max_hint_level,
        sm2_quality=quality, reviewed_at=now, study_date=today,
    ))
    db.commit()  # 상태 갱신과 기록 추가가 함께 저장된다
    logger.info("퀴즈 제출 user_id=%s word_id=%s result=%s hint=%s", user.id, word_id, result, max_hint_level)
    return AnswerResponse(
        result=result, recorded=True, practice=False, sm2_quality=quality, interval_days=new_state.interval_days,
        next_review_date=state_row.next_review_date, correct_answer=correct_answer,
        remaining_due_count=_due_count(db, user.id, today),
    )
