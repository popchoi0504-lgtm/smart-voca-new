# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 오늘 할 것·새 단어·플래시카드·설정 API (인터페이스 정의서 4.2·4.3, FR-STUDY-01~06)
# 파일 위치: src/backend/app/routers/study.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.study import (
    FlashcardRequest, FlashcardResponse, NewWordsResponse, SettingsRequest, TodayResponse, UserResponse,
)
from app.services import auth_service, study_service

# 두 주소 묶음(/study, /me)을 한 파일에 둔다: 둘 다 "내 학습"에 관한 API 이고 모두 로그인 필요
study_router = APIRouter(prefix="/study", tags=["학습"])
me_router = APIRouter(prefix="/me", tags=["내 설정"])


@study_router.get("/today", response_model=TodayResponse)
def today(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return study_service.get_today(db, current_user)


@study_router.get("/new", response_model=NewWordsResponse)
def new_words(
    limit: int = Query(10, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return NewWordsResponse(items=study_service.get_new_words(db, current_user, limit))


@study_router.post("/flashcard", response_model=FlashcardResponse)
def flashcard(body: FlashcardRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return study_service.submit_flashcard(db, current_user, body.word_id, body.rating)


@me_router.patch("/settings", response_model=UserResponse)
def update_settings(
    body: SettingsRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    user = study_service.update_daily_new_limit(db, current_user, body.daily_new_limit)
    return UserResponse(user=auth_service.to_user_out(user))
