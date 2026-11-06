# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 학습 기록 요약 API (인터페이스 정의서 4.5, FR-PROG-02~05)
# 파일 위치: src/backend/app/routers/progress.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.progress import LearnedWordsResponse, ProgressSummaryResponse
from app.services import progress_service

router = APIRouter(prefix="/progress", tags=["학습 기록"])


@router.get("/summary", response_model=ProgressSummaryResponse)
def summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return progress_service.get_summary(db, current_user)


@router.get("/words", response_model=LearnedWordsResponse)
def learned_words(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return progress_service.get_learned_words(db, current_user)
