# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 퀴즈 문제 목록·힌트·답 제출 API (인터페이스 정의서 4.4)
# 파일 위치: src/backend/app/routers/quiz.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.quiz import AnswerRequest, AnswerResponse, HintRequest, HintResponse, QuizQueueResponse
from app.services import quiz_service

router = APIRouter(prefix="/quiz", tags=["퀴즈"])


@router.get("/queue", response_model=QuizQueueResponse)
def queue(
    limit: int = Query(10, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return quiz_service.get_queue(db, current_user, limit)


@router.post("/{word_id}/hint", response_model=HintResponse, response_model_exclude_unset=True)
def hint(word_id: int, body: HintRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return quiz_service.get_hint(db, current_user, word_id, body.level)


@router.post("/{word_id}/answer", response_model=AnswerResponse)
def answer(
    word_id: int, body: AnswerRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return quiz_service.submit_answer(db, current_user, word_id, body.answer, body.max_hint_level)
