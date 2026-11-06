# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - AI 선생님 업무 규칙: 켜짐·단어 범위·하루 횟수 검사 후 담당자에게 질문 (FR-AI-02~06, NFR-AI-02·03)
# 파일 위치: src/backend/app/services/ai_service.py
import logging
import time

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.ai.prompts import SYSTEM_INSTRUCTION, build_user_message
from app.ai.provider import AiUnavailable, TeacherProvider
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.timeutil import now_utc, today_kst
from app.models.ai_usage import AiUsage
from app.models.user import User
from app.models.user_word import UserWord
from app.models.word import Word
from app.schemas.ai import TeacherRequest, TeacherResponse
from app.services.study_service import _is_premium, _plan_word_limit

logger = logging.getLogger("smart_voca.ai")

UNAVAILABLE_MESSAGE = "지금은 AI 선생님이 답할 수 없어요. 잠시 후 다시 물어봐 주세요."


def _daily_limit(user: User) -> int:
    settings = get_settings()
    return settings.ai_premium_daily_limit if _is_premium(user, now_utc()) else settings.ai_free_daily_limit


def get_usage_today(db: Session, user: User) -> tuple[int, int]:
    """(하루 한도, 오늘 쓴 횟수). 설정 화면의 이용권 요약용 — 횟수를 바꾸지 않고 읽기만 한다."""
    used = db.scalar(select(AiUsage.call_count).where(AiUsage.user_id == user.id, AiUsage.usage_date == today_kst()))
    return _daily_limit(user), used or 0


def _reserve_call(db: Session, user_id: int, usage_date, limit: int) -> int | None:
    """오늘 횟수를 1 늘린다. 한도에 이미 닿았으면 None. 확인과 증가를 SQL 한 문장으로 해서 동시에 눌러도 한도를 넘지 않는다."""
    statement = (
        insert(AiUsage)
        .values(user_id=user_id, usage_date=usage_date, call_count=1)
        .on_conflict_do_update(
            index_elements=[AiUsage.user_id, AiUsage.usage_date],
            set_={"call_count": AiUsage.call_count + 1},
            where=AiUsage.call_count < limit,
        )
        .returning(AiUsage.call_count)
    )
    new_count = db.scalar(statement)
    db.commit()
    return new_count


def _refund_call(db: Session, user_id: int, usage_date) -> None:
    """답을 못 받았을 때 미리 차감한 횟수를 돌려준다(실패한 호출은 횟수에 세지 않는다, FR-AI-06)."""
    db.execute(
        update(AiUsage)
        .where(AiUsage.user_id == user_id, AiUsage.usage_date == usage_date)
        .values(call_count=func.greatest(AiUsage.call_count - 1, 0))
    )
    db.commit()


def _get_askable_word(db: Session, user: User, request: TeacherRequest) -> Word:
    """질문할 수 있는 단어인지 확인한다.

    새 단어 화면: 요금제 범위 안의 단어만. 퀴즈 화면: 이미 배운 단어만(퀴즈 API 와 같은 규칙).
    "문제를 푼 뒤에만"은 화면에서 막는다. 서버는 풀이 여부를 믿을 만하게 알 수 없다(오답 뒤 정답은 기록하지 않는 연습 처리라서).
    """
    word = db.get(Word, request.word_id)
    if word is None:
        raise AppError(404, "WORD_NOT_FOUND", "존재하지 않는 단어입니다.")
    if request.context == "quiz":
        if db.get(UserWord, (user.id, word.id)) is None:
            raise AppError(409, "WORD_NOT_LEARNED", "아직 학습하지 않은 단어입니다.")
    elif word.frequency_rank > _plan_word_limit(db, user, now_utc()):
        raise AppError(403, "WORD_NOT_AVAILABLE", "현재 요금제에서 볼 수 없는 단어입니다.")
    return word


def ask_teacher(db: Session, user: User, request: TeacherRequest, provider: TeacherProvider) -> TeacherResponse:
    if not get_settings().ai_teacher_enabled:
        raise AppError(503, "AI_UNAVAILABLE", UNAVAILABLE_MESSAGE)
    word = _get_askable_word(db, user, request)

    limit = _daily_limit(user)
    usage_date = today_kst()
    used = _reserve_call(db, user.id, usage_date, limit)
    if used is None:
        raise AppError(429, "AI_LIMIT_REACHED", f"오늘 쓸 수 있는 {limit}회를 모두 썼어요. 프리미엄이면 더 물어볼 수 있어요.")

    started = time.perf_counter()
    try:
        answer = provider.ask(SYSTEM_INSTRUCTION, build_user_message(word, request.kind, request.question))
    except AiUnavailable as error:
        _refund_call(db, user.id, usage_date)
        # 질문 원문은 남기지 않는다. 누가 어떤 단어·종류로 물었고 어떻게 끝났는지만 남긴다
        logger.warning("AI 선생님 실패 user_id=%s word_id=%s kind=%s provider=%s 원인=%s",
                       user.id, word.id, request.kind, provider.name, error)
        raise AppError(503, "AI_UNAVAILABLE", UNAVAILABLE_MESSAGE) from error
    except Exception:
        _refund_call(db, user.id, usage_date)
        raise

    logger.info("AI 선생님 성공 user_id=%s word_id=%s kind=%s context=%s provider=%s (%.0fms) 남은횟수=%s",
                user.id, word.id, request.kind, request.context, provider.name,
                (time.perf_counter() - started) * 1000, limit - used)
    return TeacherResponse(answer=answer, remaining_today=limit - used, daily_limit=limit)
